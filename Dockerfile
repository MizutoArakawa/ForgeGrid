# ベースイメージとして python v3.10 を使用する
FROM python:3.13.7-slim

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    openssh-server \
    tzdata \
    git \
    wget \
    curl \
    iputils-ping \
    net-tools \
    procps \
    build-essential \    
    && rm -rf /var/lib/apt/lists/*

# タイムゾーンの設定（例：Asia/Tokyo）
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 以降の RUN, CMD コマンドで使われる作業ディレクトリを指定する
RUN mkdir /ForgeGrid
WORKDIR /ForgeGrid

# 要件インストール
COPY requirements.txt /ForgeGrid

# pipのプロキシ設定
RUN pip install --no-cache-dir -r requirements.txt

# Docker イメージ中の環境変数を指定する
ENV NAME=ForgeGrid

# コンテナが起動したときに実行される命令を指定する
#CMD ["python", "main.py"]
CMD ["uwsgi", "--ini", "./uwsgi_ForgeGrid.ini"]
