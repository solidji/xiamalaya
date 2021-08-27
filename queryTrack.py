#!/usr/bin/env python3

# 获取专辑列表API
# https://www.ximalaya.com/revision/user/pub?page=1&pageSize=10&keyWord=&uid=16199450&orderType=2
# https://m.ximalaya.com/m-revision/common/anchor/queryAnchorAlbumsByPage?anchorId=16199450&page=2&pageSize=20&asc=false
# 获取专辑下音频列表
# https://www.ximalaya.com/revision/album/v1/getTracksList?albumId=12285737&pageNum=1
# https://mobile.ximalaya.com/mobile/v1/album/track?albumId=12285737&device=android&isAsc=true&pageId=1&pageSize=20
# https://www.ximalaya.com/revision/album?albumId=12285737
# 获取音频下载地址
# http://mobile.ximalaya.com/v1/track/baseInfo?device=iPhone&trackId=12285737
# 获取主播信息
# https://www.ximalaya.com/mobile/v1/artist/intro?device=android&toUid=16199450
# 直接获取声音列表
# https://www.ximalaya.com/revision/user/track?page=1&pageSize=10&keyWord=&uid=16199450&orderType=2
# https://m.ximalaya.com/m-revision/page/anchor/queryAnchorPage/16199450?pageSize=20&tabType=1
# http://m.ximalaya.com/m-revision/common/anchor/queryAnchorTracksByPage?anchorId=16199450&page=2&pageSize=20&asc=false

from time import sleep

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/77.0.3865.120 Safari/537.36"
)
DB_FILE = "./tracks.db"
DOWNLOAD_PATH = "./downloads"
# DOWNLOAD_PATH = "/Volumes/Data2T/music/Wendy"


def createDBTable(reset=False):
    import os
    import sqlite3

    # 重置数据库
    if reset and os.path.isfile(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 如果表不存在则创建数据库表
    # 综合考虑，2+3接口组合效率比较高又能取全，虽然下载地址只有m4a版本
    # 1.track列表，取自接口/revision/user/track，包含albumTitle但限制最多maxCount:9990条，弃用
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS track(trackId int primary key, title varchar(20), trackUrl varchar(20), \
          albumId int, albumTitle varchar(20), albumUrl varchar(20), \
          anchorUid int, anchorUrl varchar(20), nickname varchar(20), \
          durationAsString varchar(20), isPaid INTEGER, isVideo INTEGER, isDownload INTEGER)"
    )
    # 2.track列表，取自接口queryAnchorTracksByPage，信息少一些但没有maxCount限制,同时自带一个m4a的下载地playPath址
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS trackInfo(trackId int primary key, title varchar(20), playPath varchar(20), \
          albumId int, albumTitle varchar(20), anchorUid int, \
          duration int, isPaid INTEGER, isVideo INTEGER, isDownload INTEGER)"
    )
    # 3.album列表,取自接口queryAnchorAlbumsByPage，主要是补albumTitle
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS album(albumId int primary key, albumTitle varchar(20), \
          shortIntro varchar(20), trackCount int)"
    )
    # 4.track单条下载信息,取自接口/v1/track/baseInfo，有各种格式的下载地址,也带albumTitle.看需要单条的取
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS trackDetail(trackId int primary key, title varchar(20), intro varchar(20),\
          anchorUid int, albumId int, albumTitle varchar(20), duration int,\
          playUrl32 varchar(20), playUrl64 varchar(20), downloadUrl varchar(20), \
          playPathAacv164 varchar(20),playPathAacv224 varchar(20), downloadAacUrl varchar(20))"
    )


def queryAnchorTracksByPage(args, page=1, pageSize=100):
    import sqlite3
    import requests
    import json

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 2.track列表，取自接口queryAnchorTracksByPage，信息少一些但没有maxCount限制,同时自带一个m4a的下载地playPath址
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS trackInfo(trackId int primary key, title varchar(20), playPath varchar(20), \
          albumId int, albumTitle varchar(20), anchorUid int, \
          duration int, isPaid INTEGER, isVideo INTEGER, isDownload INTEGER)"
    )

    totalCount = 33987  # 目前是33987
    # pageSize = 100  # 最大30 or 100
    # page = 1  # 从1开始
    while totalCount > (page - 1) * pageSize:
        # queryUrl = "https://www.ximalaya.com/revision/user/track?page={}&pageSize={}&uid={}".format(
        #     page, pageSize, args.uid
        # )
        queryUrl = "https://m.ximalaya.com/m-revision/common/anchor/queryAnchorTracksByPage?anchorId={}&page={}&pageSize={}&asc=false".format(
            args.uid, page, pageSize
        )
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(queryUrl, headers=headers)

        js = json.loads(response.content)
        pageSize = js["data"]["pageSize"]
        totalCount = js["data"]["totalCount"]  # 一直循环到所有

        trackList = js["data"]["trackDetailInfos"]
        print(
            "🚀 ~ func: queryTracksInfo ~ page: {} count: {} \n track: {}. \n".format(
                str(page), len(trackList), trackList[0]
            )
        )
        # 过滤掉中文字符 or boolean
        for trackInto in trackList:
            track = trackInto["trackInfo"]
            isPaid = track["isPaid"]
            isVideo = track["isVideo"]

            # for track in trackList:
            # print("🚀 ~ file: queryTrack.py ~ line 113 ~ track", track)
            # 添加数据
            # cursor.execute(r"insert into track values ('A-001', 'Adam', 95)")
            cursor.execute(
                "insert OR IGNORE into trackInfo values (?,?,?,?,?,?,?,?,?,?)",
                (
                    track["id"],
                    track["title"],
                    track["playPath"],
                    track["albumId"],
                    track["albumTitle"],
                    track["anchorId"],
                    track["duration"],
                    1 if track["isPaid"] else 0,
                    1 if track["isVideo"] else 0,
                    0,
                ),
            )
        page = js["data"]["page"] + 1
        sleep(0.5)
        # track.trackId, track.title,track.trackUrl,track.albumId,track.albumTitle,track.albumUrl,track.anchorUid,track.anchorUrl,track.nickname,track.durationAsString,track.isPaid,track.isVideo,track.isDownload

    # 安全关闭数据库连接
    cursor.close()
    conn.commit()
    conn.close()


def queryAnchorAlbumsByPage(args, page=1, pageSize=20):
    import sqlite3
    import requests
    import json

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 3.album列表,取自接口queryAnchorAlbumsByPage，主要是补albumTitle
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS album(albumId int primary key, albumTitle varchar(20), \
          shortIntro varchar(20), trackCount int)"
    )

    totalCount = 672  # 目前是627
    # pageSize = 20  # 最大20
    # page = 1  # 从1开始
    while totalCount > (page - 1) * pageSize:
        # queryUrl = "https://www.ximalaya.com/revision/user/track?page={}&pageSize={}&uid={}".format(
        #     page, pageSize, args.uid
        # )
        queryUrl = "https://m.ximalaya.com/m-revision/common/anchor/queryAnchorAlbumsByPage?anchorId={}&page={}&pageSize={}&asc=false".format(
            args.uid, page, pageSize
        )
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(queryUrl, headers=headers)

        js = json.loads(response.content)
        pageSize = js["data"]["pageSize"]
        totalCount = js["data"]["totalCount"]  # 一直循环到所有

        albumList = js["data"]["albumBriefDetailInfos"]
        print(
            "🚀 ~ func: queryAlbumInfo ~ page: {} count: {} \n track: {}. \n".format(
                str(page), len(albumList), albumList[0]
            )
        )
        # 过滤掉中文字符 or boolean
        for albumInto in albumList:
            album = albumInto["albumInfo"]
            # 添加数据
            cursor.execute(
                "insert OR IGNORE into album values (?,?,?,?)",
                (
                    album["id"],
                    album["title"],
                    album["shortIntro"],
                    albumInto["statCountInfo"]["trackCount"],
                ),
            )
        page = js["data"]["page"] + 1
        sleep(0.5)
        # track.trackId, track.title,track.trackUrl,track.albumId,track.albumTitle,track.albumUrl,track.anchorUid,track.anchorUrl,track.nickname,track.durationAsString,track.isPaid,track.isVideo,track.isDownload

    # 安全关闭数据库连接
    cursor.close()
    conn.commit()
    conn.close()


def getDownloadList(limit=6):
    import sqlite3

    result = []
    # 读取数据库中未下载完成的trackID, albumID, trackTitle
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "select trackID, title, albumID from trackInfo where isVideo = 0 AND isPaid = 0 AND isDownload = 0 order by albumID limit :limit",
        {"limit": limit},
    )  # {"isPaid": 0, "isVideo":0, "isDownload": 0}
    tracks = cursor.fetchall()
    for row in tracks:
        trackID = row[0]
        trackTitle = row[1]
        albumID = row[2]
        # 从album中获取albumTitle
        cursor.execute(
            "select albumId, albumTitle from album where albumID=:albumID",
            {"albumID": albumID},
        )
        album = cursor.fetchone()
        if not album:
            albumTitle = str(albumID)
            print("album {} 已删除".format(albumID))
        else:
            albumTitle = album[1]
        # print(trackID, album_title, trackTitle)
        result.append((trackID, albumTitle, trackTitle))
    # 安全关闭数据库连接
    cursor.close()
    conn.close()
    return result


def download_media_file(url, file_name):
    import os
    import pycurl

    if os.path.isfile(file_name):
        print(f"already downloaded: {file_name}")
        return

    # open in binary mode
    print(f"start download: {file_name}")
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.USERAGENT, USER_AGENT)
    # c.setopt(c.VERBOSE, True)

    temp_file = "%s.temp" % file_name
    # Setup writing
    if os.path.exists(temp_file):
        f = open(temp_file, "ab")
        c.setopt(pycurl.RESUME_FROM, os.path.getsize(temp_file))
    else:
        f = open(temp_file, "wb")

    c.setopt(c.WRITEDATA, f)
    try:
        c.perform()
    finally:
        c.close()
        f.close()

    os.rename(temp_file, file_name)
    print(f"download done: {file_name}")


def downloadTrack(track_info):
    # 请求接口/v1/track/baseInfo, 获取mp3格式下载地址playUrl64
    import os
    import requests
    import json
    import sqlite3

    trackID, albumTitle, trackTitle = track_info

    album_path = os.path.join(DOWNLOAD_PATH, albumTitle)
    os.makedirs(album_path, exist_ok=True)
    queryUrl = (
        "http://mobile.ximalaya.com/v1/track/baseInfo?device=iPhone&trackId={}".format(
            trackID
        )
    )
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(queryUrl, headers=headers)
    js = json.loads(response.content)
    play_path = js["playUrl64"] or js["playUrl32"]
    _, file_extension = os.path.splitext(play_path)
    file_name = "%s%s" % (trackTitle, file_extension)
    path_name = os.path.join(album_path, file_name)
    print(trackID, play_path, path_name)

    # 下载文件，成功后设置下载完成标记到数据库
    try:
        download_media_file(play_path, path_name)
    except Exception as ex:
        print(ex)
        # pass
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trackInfo SET isDownload = 1 WHERE trackId =:trackId",
        {"trackId": trackID},
    )

    # 安全关闭数据库连接
    cursor.close()
    conn.commit()
    conn.close()
    return True


def main():
    import os
    import argparse
    from concurrent.futures import ThreadPoolExecutor
    from functools import partial

    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", "-u", help="anchor uid", type=int, default=16199450)
    args = parser.parse_args()
    print("🚀 ~ file: queryTrack.py ~ line 32 ~ args {}.".format(args))

    # createDBTable() # 第一次运行时创建数据库与表
    # queryAnchorTracksByPage(args) # 获取track列表，保存到trackInfo表
    # queryAnchorAlbumsByPage(args)  # 获取album列表，保存到album表

    result = getDownloadList(5)
    print(result)
    # for m in result:
    #     downloadTrack(m)
    has_error = False
    with ThreadPoolExecutor(max_workers=3) as executor:
        func = partial(downloadTrack)
        errors = executor.map(func, result)
        for err in errors:
            has_error &= err

    if has_error:
        print(
            "download is done however there are some errors occur. Please rerun the download command to retry!"
        )
    else:
        print("track {} is downloaded".format(len(result)))


if __name__ == "__main__":
    main()
