# anime-cover-crawler

这是一个用于抓取动漫封面的项目。该项目支持从多个数据源(Bilibili、AniList、MAL、Bangumi、AniDB等)抓取动漫的高清封面，并将其保存到本地。

## 功能特点

- 支持多个数据源抓取
  - Bilibili
  - AniList
  - MyAnimeList
  - Bangumi
  - AniDB
- 智能图片质量评估
  - 分辨率检测
  - 文件大小检查
  - 综合质量评分
- 自动选择最高质量图片
- 支持批量下载全部来源
- 显示详细下载信息
  - 分辨率信息
  - 文件大小
  - 质量评分
- 下载进度实时显示
- 自动重试机制
- 文件自动时间戳命名

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

### 多源下载(推荐)
```bash
python src/main_multi.py [动漫名称]
```

### 单源下载
```bash
python src/main.py [动漫名称]
```

如果不提供动漫名称参数，程序会在运行时提示输入。

## 使用示例

```bash
# 多源下载（推荐）
python src/main_multi.py "名侦探柯南"

# 运行后会显示：
找到 4 个封面:

按质量排序的结果:
1. 来源: anilist
   标题: 名探偵コナン
   分辨率: 1920x2700
   文件大小: 1.25MB
   质量评分: 6480000

2. 来源: bangumi
   标题: 名探偵コナン
   分辨率: 1400x2000
   文件大小: 0.95MB
   质量评分: 2660000

# ...其他结果
```

## 特性说明

### 图片质量评分
- 分辨率：宽度 × 高度
- 文件大小：以 MB 为单位
- 质量评分 = 宽度 × 高度 × 文件大小

### 下载选项
- 可选择只下载最高质量图片
- 支持下载所有来源的图片

## 待解决
-  myanimelist 下载失败

## 贡献

欢迎任何形式的贡献！如果您有建议或发现了错误，请提交问题或拉取请求。

## 许可证

该项目遵循 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。