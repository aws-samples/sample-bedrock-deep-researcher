# Bedrock Deep Research - 依存関係マップ

このドキュメントでは、Bedrock Deep Researchプロジェクト内の主要なコンポーネント間の依存関係を示します。

## 主要コンポーネント間の依存関係

```mermaid
graph TD
    %% メインエントリーポイント
    StreamlitApp[bedrock_deep_research.py] --> BDR[BedrockDeepResearch]
    StreamlitApp --> Models[model.py]
    
    %% コアクラスの依存関係
    BDR --> Config[config.py]
    BDR --> WebSearch[web_search.py]
    BDR --> StateModels[model.py]
    
    %% ノード間の依存関係
    BDR --> InitialResearcher[initial_researcher.py]
    BDR --> AOG[article_outline_generator.py]
    BDR --> HFP[human_feedback_provider.py]
    BDR --> SectionSubgraph[セクション処理サブグラフ]
    BDR --> CSF[completed_sections_formatter.py]
    BDR --> FSW[final_sections_writer.py]
    BDR --> AHIG[article_head_image_generator.py]
    BDR --> CFA[compile_final_article.py]
    
    %% セクション処理サブグラフ
    SectionSubgraph --> SSQG[section_search_query_generator.py]
    SectionSubgraph --> SWR[section_web_researcher.py]
    SectionSubgraph --> SW[section_writer.py]
    
    %% ウェブ検索の依存関係
    WebSearch --> Tavily[Tavily API]
    InitialResearcher --> WebSearch
    SWR --> WebSearch
    
    %% 条件付きエッジ
    CSF --> IFSW[initiate_final_section_writing.py]
    IFSW --> FSW
    
    %% 外部依存関係
    BDR --> LangGraph[LangGraph]
    AHIG --> NovaCanvas[Amazon Bedrock Nova Canvas]
    AOG --> Bedrock[Amazon Bedrock]
    SW --> Bedrock
    FSW --> Bedrock
```

## ファイルレベルの依存関係

```mermaid
graph LR
    %% メインファイル
    Main[bedrock_deep_research.py] --> Config
    Main --> Model
    Main --> BDR_Init
    
    %% コアモジュール
    BDR_Init[bedrock_deep_research/__init__.py] --> Graph
    Graph[bedrock_deep_research/graph.py] --> Config
    Graph --> Model
    Graph --> Nodes_Init
    Graph --> WebSearch
    
    %% モデルと設定
    Config[bedrock_deep_research/config.py]
    Model[bedrock_deep_research/model.py]
    Utils[bedrock_deep_research/utils.py]
    WebSearch[bedrock_deep_research/web_search.py]
    
    %% ノードモジュール
    Nodes_Init[bedrock_deep_research/nodes/__init__.py] --> IR
    Nodes_Init --> AOG
    Nodes_Init --> HFP
    Nodes_Init --> SSQG
    Nodes_Init --> SWR
    Nodes_Init --> SW
    Nodes_Init --> CSF
    Nodes_Init --> IFSW
    Nodes_Init --> FSW
    Nodes_Init --> AHIG
    Nodes_Init --> CFA
    
    %% 個別ノード
    IR[bedrock_deep_research/nodes/initial_researcher.py] --> Model
    IR --> Config
    IR --> WebSearch
    
    AOG[bedrock_deep_research/nodes/article_outline_generator.py] --> Model
    AOG --> Config
    
    HFP[bedrock_deep_research/nodes/human_feedback_provider.py] --> Model
    
    SSQG[bedrock_deep_research/nodes/section_search_query_generator.py] --> Model
    SSQG --> Config
    
    SWR[bedrock_deep_research/nodes/section_web_researcher.py] --> Model
    SWR --> WebSearch
    
    SW[bedrock_deep_research/nodes/section_writer.py] --> Model
    SW --> Config
    SW --> Utils
    
    CSF[bedrock_deep_research/nodes/completed_sections_formatter.py] --> Model
    
    IFSW[bedrock_deep_research/nodes/initiate_final_section_writing.py] --> Model
    
    FSW[bedrock_deep_research/nodes/final_sections_writer.py] --> Model
    FSW --> Config
    
    AHIG[bedrock_deep_research/nodes/article_head_image_generator.py] --> Model
    AHIG --> Config
    AHIG --> Utils
    
    CFA[bedrock_deep_research/nodes/compile_final_article.py] --> Model
```

## 外部ライブラリ依存関係

```mermaid
graph TD
    %% メインプロジェクト
    BedrockDeepResearch --> AWS_Libs
    BedrockDeepResearch --> LangChain_Libs
    BedrockDeepResearch --> UI_Libs
    BedrockDeepResearch --> Utility_Libs
    
    %% AWSライブラリグループ
    AWS_Libs --> LangchainAWS[langchain_aws]
    AWS_Libs --> Boto3[boto3]
    
    %% LangChainライブラリグループ
    LangChain_Libs --> LangGraph[langgraph]
    LangChain_Libs --> LangChainCore[langchain_core]
    
    %% UIライブラリグループ
    UI_Libs --> Streamlit[streamlit]
    UI_Libs --> Pyperclip[pyperclip]
    
    %% ユーティリティライブラリグループ
    Utility_Libs --> Pydantic[pydantic]
    Utility_Libs --> DotEnv[dotenv]
    Utility_Libs --> NestAsyncio[nest_asyncio]
    Utility_Libs --> AsyncIO[asyncio]
    Utility_Libs --> Requests[requests]
    Utility_Libs --> JSON[json]
    Utility_Libs --> OS[os]
    Utility_Libs --> UUID[uuid]
    Utility_Libs --> Logging[logging]
```

## コンポーネント間のデータフロー

```mermaid
flowchart TD
    %% 主要なデータフロー
    UserInput[ユーザー入力\n- トピック\n- 書き込みガイドライン] --> StreamlitUI
    
    StreamlitUI[Streamlitインターフェース] --> |トピック・設定| Graph
    
    Graph[BedrockDeepResearch\ngraph.py] --> |初期トピック| IR
    IR[InitialResearcher] --> |検索結果| AOG
    AOG[ArticleOutlineGenerator] --> |記事概要| HFP
    
    HFP[HumanFeedbackProvider] --> |ユーザーフィードバック| StreamlitUI
    StreamlitUI --> |フィードバック| HFP
    
    HFP --> |検証済み概要| SectionProcessor
    
    subgraph SectionProcessor[セクション処理]
        SSQG[検索クエリ生成] --> |検索クエリ| SWR
        SWR[ウェブ検索] --> |検索結果| SW
        SW[セクション作成] --> |完成セクション| Output
    end
    
    SectionProcessor --> |完成セクション| CSF
    CSF[CompletedSectionsFormatter] --> |すべてのセクション| FSW
    FSW[FinalSectionsWriter] --> |最終セクション| AHIG
    AHIG[ArticleHeadImageGenerator] --> |画像付きデータ| CFA
    CFA[CompileFinalArticle] --> |最終記事| StreamlitUI
    
    StreamlitUI --> |最終記事| UserOutput[ユーザー出力\n- 完成記事\n- ヘッダー画像]
```

この依存関係マップは、各モジュールがどのように相互に関連し、データがシステム内でどのように流れるかを視覚化しています。BedrockDeepResearchクラスがワークフローの中心となり、各ノードが特定の処理を担当しています。外部サービス（Amazon Bedrock、Tavily API）への依存関係も明示されています。 