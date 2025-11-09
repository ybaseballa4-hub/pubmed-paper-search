import os
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import xml.etree.ElementTree as ET
from datetime import datetime
import tempfile
import time

# ✅ ページ設定（最初に1回だけ呼び出す）
st.set_page_config(
    page_title="RT-LitSearch - 整形外科論文要約",
    page_icon="🏥",
    layout="wide",
)

# ✅ スタイル（CSS）: set_page_config の後に置く
st.markdown(
    """
    <style>
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-size: 1.4rem;
        line-height: 1.6rem;
    }
    button[kind="primary"] {
        font-size: 1.2rem !important;
        padding: 1rem 2rem !important;
    }
    .stMarkdown {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
    }
    a {
        color: #0066cc !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ 環境変数
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NIH_EMAIL = os.getenv("NIH_EMAIL")


class PubMedSearcher:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = NIH_EMAIL or ""

    def search_papers(self, query, max_results=5):
        """PubMedで論文を検索"""
        try:
            search_url = f"{self.base_url}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "sort": "pub_date",
                "retmode": "xml"
            }
            if self.email:
                search_params["email"] = self.email

            response = requests.get(search_url, params=search_params)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]
            if not pmids:
                return []
            return self._fetch_paper_details(pmids)
        except Exception as e:
            print(f"PubMed検索エラー: {e}")
            return []

    def _fetch_paper_details(self, pmids):
        """PMIDから論文詳細を取得"""
        try:
            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            }
            if self.email:
                fetch_params["email"] = self.email

            response = requests.get(fetch_url, params=fetch_params)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            papers = []
            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
            return papers
        except Exception as e:
            print(f"論文詳細取得エラー: {e}")
            return []

    def _parse_article(self, article):
        """XML記事データをパース"""
        try:
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "タイトル不明"
            authors = []
            for author in article.findall(".//Author")[:5]:
                last_name = author.find("LastName")
                first_name = author.find("ForeName")
                if last_name is not None:
                    name = last_name.text
                    if first_name is not None:
                        name += f" {first_name.text}"
                    authors.append(name)
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "雑誌名不明"
            year_elem = article.find(".//PubDate/Year")
            year = year_elem.text if year_elem is not None else "年不明"
            abstract_elem = article.find(".//Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else ""
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
        except Exception as e:
            print(f"記事パースエラー: {e}")
            return None


class PaperSummarizer:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def summarize_paper(self, paper):
        """論文を日本語で要約"""
        try:
            prompt = f"""
以下の医学論文について、整形外科クリニックの医師・理学療法士向けに300-500字の日本語要約を作成してください。

タイトル: {paper['title']}
著者: {', '.join(paper['authors'][:3])}
雑誌: {paper['journal']} ({paper['year']})
アブストラクト: {paper['abstract'][:1000]}

要約の構成:
1. 背景・目的（1-2文）
2. 方法・介入（1-2文）
3. 結果（2-3文）
4. 臨床的示唆（1-2文）
5. 限界・注意点（1文）
"""
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは整形外科・リハビリ分野の論文要約専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"要約生成エラー: {e}")
            return "要約の生成に失敗しました。"


def search_and_summarize(query, max_results):
    if not query.strip():
        return "検索キーワードを入力してください。", None

    progress_bar = st.progress(0.0)
    status_text = st.empty()
    status_text.text("PubMedで論文を検索中...")
    progress_bar.progress(0.10)

    searcher = PubMedSearcher()
    papers = searcher.search_papers(query, max_results)
    if not papers:
        status_text.text("該当する論文が見つかりませんでした。")
        return [], None

    progress_bar.progress(0.30)

    summarizer = PaperSummarizer()
    results = []
    for i, paper in enumerate(papers):
        status_text.text(f"論文 {i+1}/{len(papers)} を要約中...")
        pct = (30.0 + 60.0 * (i + 1) / len(papers)) / 100.0
        pct = max(0.0, min(pct, 1.0))
        progress_bar.progress(pct)
        summary = summarizer.summarize_paper(paper)
        result = {
            "title": paper["title"],
            "authors": paper["authors"],
            "journal": paper["journal"],
            "year": paper["year"],
            "url": paper["url"],
            "summary": summary
        }
        results.append(result)
        time.sleep(1)

    markdown_file = generate_markdown_file(results, query)
    progress_bar.progress(1.0)
    status_text.text("検索・要約が完了しました！")
    return results, markdown_file


def generate_markdown_file(results, query):
    try:
        markdown_content = f"""# RT-LitSearch 検索結果

**検索キーワード:** {query}  
**検索日時:** {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**件数:** {len(results)}件

---
"""
        for i, result in enumerate(results, 1):
            authors_text = ", ".join(result["authors"][:3])
            if len(result["authors"]) > 3:
                authors_text += " ほか"
            markdown_content += f"""## {i}. {result["title"]}

**著者:** {authors_text}  
**雑誌:** {result["journal"]} ({result["year"]})  
**PubMed URL:** {result["url"]}

### 📋 臨床向け要約
{result["summary"]}

---
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        temp_file.write(markdown_content)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"Markdownファイル生成エラー: {e}")
        return None


def main():
    st.markdown("""
    <div style="text-align: center; color: #2c5aa0; margin-bottom: 30px;">
        <h1>🏥 RT-LitSearch</h1>
        <p style="font-size: 18px;">整形外科クリニック向け PubMed論文要約アプリ</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_area(
            "🔍 検索キーワード",
            placeholder="例: 膝OA 運動療法, shoulder impingement exercise, lumbar disc herniation",
            height=100
        )
    with col2:
        max_results = st.slider("📊 取得件数", min_value=1, max_value=10, value=5, step=1)

    if st.button("🚀 検索・要約実行", type="primary"):
        if not query.strip():
            st.error("検索キーワードを入力してください。")
        else:
            results, markdown_file = search_and_summarize(query, max_results)
            if results:
                st.markdown(f"### 📄 検索結果: \"{query}\" ({len(results)}件)")
                for i, result in enumerate(results, 1):
                    with st.expander(f"{i}. {result['title']}", expanded=True):
                        authors_text = ", ".join(result["authors"][:3])
                        if len(result["authors"]) > 3:
                            authors_text += " ほか"
                        st.markdown(f"""
                        **著者:** {authors_text}  
                        **雑誌:** {result["journal"]} ({result["year"]})  
                        **PubMed URL:** [{result["url"]}]({result["url"]})

                        ### 📋 臨床向け要約
                        {result["summary"]}
                        """)
                if markdown_file:
                    with open(markdown_file, 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                    st.download_button(
                        label="💾 Markdownファイルをダウンロード",
                        data=markdown_content,
                        file_name=f"RT-LitSearch_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown"
                    )

    st.markdown("""
    ---
    ### 💡 使い方
    1. **検索キーワードを入力**（日本語・英語どちらでも可）
    2. **取得件数を選択**（1-10件）
    3. **「検索・要約実行」ボタンをクリック**
    4. **結果を確認**し、必要に応じてMarkdownファイルをダウンロード
    """)


if __name__ == "__main__":
    if not OPENAI_API_KEY:
        st.error("⚠️ OPENAI_API_KEYが設定されていません。")
        st.info("ローカル実行の場合は.envファイルを作成してください。")
        st.stop()
    main()
