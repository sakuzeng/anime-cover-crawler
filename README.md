# anime-cover-crawler

这是一个用于抓取动漫封面的项目。该项目支持从多个数据源(Bilibili、AniList等)抓取动漫的高清封面，并将其保存到本地。

## 功能特点

- 支持多个数据源抓取(Bilibili、AniList)
- 自动重试机制
- 高清封面下载
- 文件自动时间戳命名
- 显示下载进度和文件信息

## 项目结构

```
anime-cover-crawler
├── src
│   ├── main.py                    # 单源下载入口
│   ├── main_multi.py             # 多源下载入口
│   ├── crawler
│   │   ├── __init__.py           # 爬虫包初始化文件
│   │   ├── scraper.py            # 单源爬虫实现
│   │   ├── multi_source_downloader.py  # 多源下载器
│   │   └── anime_source.py       # 数据源定义
│   ├── utils
│   │   ├── __init__.py           # 工具包初始化文件
│   │   └── helpers.py            # 辅助函数
│   └── config
│       └── config.py             # 配置文件
├── covers                        # 下载的封面保存目录
├── requirements.txt              # 项目依赖
└── README.md                     # 项目说明文档
```

## 安装依赖

在项目根目录下运行以下命令以安装所需的依赖：

```bash
pip install -r requirements.txt
```

## 运行程序

### 单源下载
```bash
python src/main.py [动漫名称]
```

### 多源下载(推荐)
```bash
python src/main_multi.py [动漫名称]
```

如果不提供动漫名称参数，程序会在运行时提示输入。

## 使用示例

```bash
# 单源下载
python src/main.py "你的名字"

# 多源下载
python src/main_multi.py "名侦探柯南"
```

## 贡献

欢迎任何形式的贡献！如果您有建议或发现了错误，请提交问题或拉取请求。

## 许可证

该项目遵循 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。