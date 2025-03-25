# anime-cover-crawler

这是一个用于抓取动漫封面的项目。该项目的主要功能是从指定的网站抓取动漫的高清封面，并将其保存到本地。

## 项目结构

```
anime-cover-crawler
├── src
│   ├── main.py
│   ├── crawler
│   │   ├── __init__.py 
│   │   └── scraper.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config
│       └── config.py
├── tests
│   └── test_scraper.py
├── requirements.txt
└── README.md
```

## 安装依赖

在项目根目录下运行以下命令以安装所需的依赖：

```
pip install -r requirements.txt
```

## 运行程序

要运行程序，请执行以下命令：

```
python src/main.py
```

## 贡献

欢迎任何形式的贡献！如果您有建议或发现了错误，请提交问题或拉取请求。

## 许可证

该项目遵循 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。