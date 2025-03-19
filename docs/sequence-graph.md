# Bedrock Deep Research - 処理シーケンス図

このドキュメントでは、Bedrock Deep Researchアプリケーションの主要な処理の流れをシーケンス図の形式で説明します。

## 全体のワークフロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as Streamlitインターフェース
    participant BDR as BedrockDeepResearch
    participant WS as WebSearch (Tavily)
    participant IM as 画像生成 (Nova Canvas)
    
    User->>UI: トピックと執筆ガイドラインを入力
    UI->>BDR: トピックとパラメータを渡す
    BDR->>WS: 初期ウェブ検索を実行
    WS-->>BDR: 検索結果を返す
    BDR->>BDR: 記事の概要を生成
    BDR-->>UI: 概要を表示
    UI-->>User: 概要をレビュー
    User->>UI: フィードバックを提供
    UI->>BDR: フィードバックを渡す
    BDR->>BDR: 概要を更新
    BDR-->>UI: 更新された概要を表示
    UI-->>User: 最終確認
    User->>UI: 概要を承認
    
    loop 各セクションに対して
        BDR->>BDR: 検索クエリを生成
        BDR->>WS: セクション固有の検索を実行
        WS-->>BDR: 検索結果を返す
        BDR->>BDR: セクションコンテンツを作成
    end
    
    BDR->>BDR: 最終セクション（概要・結論）を作成
    BDR->>IM: ヘッダー画像を生成
    IM-->>BDR: 画像を返す
    BDR->>BDR: 最終記事をコンパイル
    BDR-->>UI: 完成した記事と画像を表示
    UI-->>User: 最終記事を確認
```

## 詳細なノード間シーケンス

```mermaid
sequenceDiagram
    participant START
    participant IR as InitialResearcher
    participant AOG as ArticleOutlineGenerator
    participant HFP as HumanFeedbackProvider
    participant SBWSR as build_section_with_web_research
    participant CSF as CompletedSectionsFormatter
    participant FSW as FinalSectionsWriter
    participant AHIG as ArticleHeadImageGenerator
    participant CFA as CompileFinalArticle
    participant END
    
    START->>IR: 開始
    IR->>AOG: 初期検索結果
    AOG->>HFP: 記事概要
    HFP->>SBWSR: 検証済み概要
    
    loop 各セクションに対して
        SBWSR->>SBWSR: セクション処理サブグラフ実行
    end
    
    SBWSR->>CSF: 完成したセクション
    
    alt すべてのセクションが完成
        CSF->>FSW: 概要と結論セクション作成
        FSW->>AHIG: 最終セクション追加
        AHIG->>CFA: ヘッダー画像を追加
        CFA->>END: 完成
    else セクションが未完成
        CSF->>SBWSR: 続行
    end
```

## セクション処理サブグラフ

```mermaid
sequenceDiagram
    participant START
    participant SSQG as SectionSearchQueryGenerator
    participant SWR as SectionWebResearcher
    participant SW as SectionWriter
    participant END
    
    START->>SSQG: セクション情報
    SSQG->>SWR: 検索クエリ
    SWR->>SW: ウェブ検索結果
    SW->>END: 完成したセクション
```

## ユーザーインタラクションフロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant IF as InitialForm
    participant OR as OutlineReview
    participant FR as FinalResult
    
    User->>IF: トピックと設定入力
    IF->>OR: 概要生成
    
    loop フィードバックループ
        OR-->>User: 概要を表示
        User->>OR: フィードバック提供
        OR->>OR: 概要を更新
    end
    
    OR->>FR: 概要を承認
    FR->>FR: 記事生成処理
    FR-->>User: 最終記事と画像を表示
    
    alt コピー
        User->>FR: クリップボードにコピー
    else やり直し
        User->>IF: 新しい記事開始
    end
```

この図はLangGraphを使用した処理フローを示しており、BedrockDeepResearchクラス内にある複数のノードがお互いにデータを渡しながら、記事の生成プロセスを段階的に進めていくことを表しています。ユーザーインターフェースとバックエンドのワークフロー間の相互作用も含まれています。 