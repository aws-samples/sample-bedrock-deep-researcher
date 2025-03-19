# Bedrock Deep Research - プロジェクト構造

このドキュメントでは、Bedrock Deep Researchプロジェクトのディレクトリ構造と各ファイルの役割について詳細に説明します。

## ディレクトリ構造

```
sample-bedrock-deep-researcher/
├── .git/                            # Gitリポジトリ情報
├── .gitignore                       # Gitが無視するファイルの設定
├── .pre-commit-config.yaml          # Pre-commitフックの設定
├── CODE_OF_CONDUCT.md               # 行動規範
├── CONTRIBUTING.md                  # コントリビューションガイドライン
├── LICENSE                          # ライセンス情報（MIT-0）
├── README.md                        # プロジェクト説明
│
├── bedrock_deep_research.py         # メインのStreamlitアプリケーションエントリーポイント
│
├── bedrock_deep_research/           # コアモジュールディレクトリ
│   ├── __init__.py                  # BedrockDeepResearchクラスをエクスポート
│   ├── config.py                    # 設定パラメータと定数の定義
│   ├── graph.py                     # LangGraphを使用したコアワークフロー構築
│   ├── model.py                     # Pydanticモデルの定義（記事、セクションなど）
│   ├── utils.py                     # ユーティリティ関数
│   ├── web_search.py                # Tavily APIを使用したウェブ検索機能
│   │
│   └── nodes/                       # ワークフローの各ノード実装
│       ├── __init__.py              # ノードのエクスポート
│       ├── article_head_image_generator.py    # ヘッダー画像生成
│       ├── article_outline_generator.py       # 記事の概要生成
│       ├── compile_final_article.py           # 最終記事のコンパイル
│       ├── completed_sections_formatter.py    # 完成したセクションのフォーマット
│       ├── final_sections_writer.py           # 最終セクション（概要、結論）の執筆
│       ├── human_feedback_provider.py         # 人間からのフィードバック処理
│       ├── initial_researcher.py              # 初期ウェブ調査
│       ├── initiate_final_section_writing.py  # 最終セクション執筆の開始判断
│       ├── section_search_query_generator.py  # セクション毎の検索クエリ生成
│       ├── section_web_researcher.py          # セクション毎のウェブ検索実行
│       └── section_writer.py                  # セクションのコンテンツ執筆
│
├── docs/                            # プロジェクトドキュメント
│   ├── project-brief.md             # プロジェクト概要
│   ├── project-structure.md         # このファイル
│   ├── sequence-graph.md            # 処理シーケンス図
│   ├── dependency-map.md            # コード間の依存関係マップ
│   └── specification.md             # 技術仕様と制約
│
├── env.tmp                          # 環境変数テンプレート
├── poetry.lock                      # Poetryの依存関係ロックファイル
├── pyproject.toml                   # プロジェクト設定と依存関係
│
└── static/                          # 静的アセット（画像等）
    ├── agent_walkthrough.png        # エージェントフロー図
    ├── article_config.png           # 記事設定インターフェース
    ├── article_outline_review.png   # 概要レビューインターフェース
    └── final_article_view.png       # 最終記事表示インターフェース
```

## 主要ファイルの説明

### ルートディレクトリ

- **bedrock_deep_research.py**: Streamlitアプリケーションのエントリーポイント。ユーザーインターフェースの構築、フォーム処理、記事の生成と表示を担当します。

- **env.tmp**: 環境変数のテンプレートファイル。Tavily APIキーなどの設定に使用されます。

- **pyproject.toml**: Poetry依存関係管理と設定ファイル。プロジェクトの依存パッケージとPython要件を定義しています。

- **poetry.lock**: Poetry依存関係のロックファイル。正確なパッケージバージョンを保証します。

### bedrock_deep_research/ モジュール

- **__init__.py**: BedrockDeepResearchクラスをエクスポートして、外部からのアクセスを可能にします。

- **config.py**: 設定定数と構成クラス。デフォルトの記事構造、書き込みガイドライン、サポートされているモデルなどを定義しています。

- **graph.py**: BedrockDeepResearchクラスの実装。LangGraphを使用して全体のワークフローをオーケストレーションします。

- **model.py**: アプリケーションのデータモデル定義。Section、Outline、ArticleStateなどのPydanticモデルを含みます。

- **utils.py**: 共通ユーティリティ関数。ファイル操作や日付処理などの補助機能を提供します。

- **web_search.py**: Tavily APIを利用したウェブ検索機能の実装。検索結果の取得と処理を担当します。

### nodes/ サブモジュール

各ノードは、LangGraphワークフローの特定のステップを担当するコンポーネントです。主要なノードは以下のとおりです：

- **article_outline_generator.py**: 初期リサーチをもとに記事の概要（タイトルとセクション）を生成します。

- **human_feedback_provider.py**: ユーザーからのフィードバックを処理して、記事の概要を更新します。

- **section_search_query_generator.py**: 各セクションに対する最適な検索クエリを生成します。

- **section_web_researcher.py**: セクション固有の検索クエリに基づいてウェブ検索を実行します。

- **section_writer.py**: 検索結果を使用してセクションのコンテンツを生成します。

- **final_sections_writer.py**: 他のセクションの内容に基づいて、概要と結論を作成します。

- **article_head_image_generator.py**: 記事のタイトルとコンテンツに基づいて、関連するヘッダー画像を生成します。

- **compile_final_article.py**: 生成されたすべてのセクションを結合して最終的な記事を作成します。

## 処理の流れ

1. **bedrock_deep_research.py** でユーザー入力を収集
2. **BedrockDeepResearch** クラス（graph.py）でワークフローを初期化
3. ワークフロー内の各ノードが順番に実行され、研究と記事生成を行う
4. 最終的な記事と画像がStreamlitインターフェースに表示される

このモジュール構造は、関心事の分離を促進し、コードの再利用性と保守性を向上させます。各コンポーネントは特定の責任を持ち、明確なインターフェースを通じて相互作用します。 