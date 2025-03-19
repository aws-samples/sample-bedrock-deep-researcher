# Bedrock Deep Research - プロジェクト概要

## システムの目的

Bedrock Deep Researchは、Amazon Bedrock、LangGraph、LangChain AWSライブラリを活用したStreamlitベースのアプリケーションで、AIを駆使した記事/レポート生成を自動化します。このシステムは、ウェブ検索、構造化されたコンテンツ生成、人間からのフィードバックを組み合わせて、包括的で十分に調査された記事とそれに付随するヘッダー画像（[Amazon Bedrock Nova Canvas](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html)によって生成）を作成します。

## 概要

Bedrock Deep Researchは、LangChainの[Deep Researcher](https://github.com/langchain-ai/open_deep_research/tree/main)をインスピレーションとしています。以下の主要な機能を提供します：

1. **自動化された調査**: 関連情報を収集するための的を絞ったウェブ検索を実行
2. **構造化されたコンテンツ生成**: まとまりのある記事の概要と詳細なセクションコンテンツを作成
3. **インタラクティブなフィードバックループ**: 記事の概要を改善するために人間からのフィードバックを取り入れる
4. **AIによる画像生成**: 視覚的な魅力のための関連ヘッダー画像を生成

## 技術スタック

- **フロントエンド**: Streamlit（Pythonベースのウェブインターフェース）
- **AIモデル**: Amazon Bedrock（Claude 3.5 Haiku、Claude 3.5 Sonnet v2、Claude 3.7 Sonnet）
- **画像生成**: Amazon Bedrock Nova Canvas
- **オーケストレーション**: LangGraph（ワークフローの管理）
- **LLM統合**: LangChain AWS（Amazon Bedrockとの統合）
- **ウェブ検索**: Tavily API（研究目的）

## ワークフロー概要

1. ユーザーがトピックと記事作成のガイドラインを入力
2. システムが初期ウェブ調査を実行
3. 収集された情報に基づいて記事の概要を生成
4. ユーザーが概要にフィードバックを提供し、承認
5. 各セクションについて、さらなる調査と詳細なコンテンツ生成を実行
6. 全セクションを1つの記事にコンパイル
7. 関連するヘッダー画像を生成
8. 最終的な記事をユーザーに提示

このアプリケーションは、研究プロセスと記事作成プロセスを大幅に合理化し、高品質で十分に調査されたコンテンツの迅速な生成を可能にします。 