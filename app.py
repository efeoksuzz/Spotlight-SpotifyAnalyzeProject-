from flask import Flask, render_template, request, jsonify
import pandas as pd
from pandas import Categorical
import zipfile, io

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def upload_file():  # BURAYA BAK
    return render_template("spot.html")


@app.route("/ds", methods=["POST"])
def stats_data():
    file = request.files['file']

    dfs = []
    with zipfile.ZipFile(file.stream) as z:
        for name in z.namelist():
            if name.lower().endswith('.json'):
                with z.open(name) as f:
                    raw = f.read()

                    df_part = pd.read_json(io.BytesIO(raw))

                dfs.append(df_part)

    if not dfs:
        return jsonify({"error": "Zip içinde JSON bulunamadı"}), 400

    df_all = pd.concat(dfs, ignore_index=True)

    drop_cols = ['platform', 'ms_played', 'conn_country', 'ip_addr',
                 'spotify_track_uri', 'episode_name', 'episode_show_name',
                 'spotify_episode_uri', 'audiobook_title', 'audiobook_uri',
                 'audiobook_chapter_uri', 'audiobook_chapter_title',
                 'reason_start', 'reason_end', 'shuffle', 'skipped',
                 'offline', 'offline_timestamp', 'incognito_mode']
    df = df_all.drop(columns=drop_cols, errors='ignore')

    # ---- İstatistikler ----
    top_songs = df['master_metadata_track_name'].value_counts().head(10)
    top_artists = df['master_metadata_album_artist_name'].value_counts().head(10)
    top_albums = df['master_metadata_album_album_name'].value_counts().head(10)

    df['hour'] = pd.to_datetime(df['ts']).dt.hour
    hourly = df['hour'].value_counts().sort_index()

    df['year'] = pd.to_datetime(df['ts']).dt.year
    yearly = df['year'].value_counts().sort_index()

    ordered_days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    df['day_name'] = pd.to_datetime(df['ts']).dt.day_name(locale="tr_TR")
    df['day_name'] = Categorical(df['day_name'], categories=ordered_days, ordered=True)
    daily_counts = df['day_name'].value_counts().sort_index()

    ordered_months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim',
                      'Kasım', 'Aralık']
    df['month'] = pd.to_datetime(df['ts']).dt.month_name(locale="tr_TR")
    df['month'] = Categorical(df['month'], categories=ordered_months, ordered=True)
    monthly = df['month'].value_counts().sort_index()

    data = {
        "top_songs": {"labels": top_songs.index.tolist(), "values": [int(x) for x in top_songs.values.tolist()]},
        "top_artists": {"labels": top_artists.index.tolist(),
                        "values": [int(x) for x in top_artists.values.tolist()]},
        "top_albums": {"labels": top_albums.index.tolist(), "values": [int(x) for x in top_albums.values.tolist()]},
        "hourly": {"labels": [str(x) for x in hourly.index.tolist()],
                   "values": [int(x) for x in hourly.values.tolist()]},
        "yearly": {"labels": [str(x) for x in yearly.index.tolist()],
                   "values": [int(x) for x in yearly.values.tolist()]},
        "daily": {"labels": [str(x) for x in daily_counts.index.tolist()],
                  "values": [int(x) for x in daily_counts.values.tolist()]},
        "monthly": {"labels": [str(x) for x in monthly.index.tolist()],
                    "values": [int(x) for x in monthly.values.tolist()]}
    }
    return jsonify(data), 200


if __name__ == "__main__":
    app.run()
