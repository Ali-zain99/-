🚀 Harnessing LangExtract + OpenAI API for Smarter Web Scraping
I recently tried out LangExtract, a powerful open‑source Python library by Google, paired with the OpenAI API, and I'm impressed—it’s hands down one of the best tools I’ve used for intelligent web scraping and structured data extraction.

What Is LangExtract?
LangExtract is a Gemini‑powered library built to take unstructured text—from websites, documents, or feedback—and turn it into structured, grounded data. You define:

A prompt with extraction requirements

Few‑shot examples showing the schema
and LangExtract handles the rest, even across long documents using chunking and multi‑pass processing 
Google for Developers
+8
Google Developers Blog
+8
ADaSci
+8
GitHub
+1
.

Why It Stands Out
Source grounding: Each extraction is tied to exact character offsets, so you can trace where every piece of data came from 
Google Developers Blog
+2
ADaSci
+2
.

Schema enforcement: Controlled generation ensures consistent output formats, reducing hallucinations and mismatches 
Google Developers Blog
+2
ADaSci
+2
.

Long‑text handling: Optimized for million‑token documents via chunking and parallel passes, boosting recall 
GitHub
+2
Reddit
+2
.

Fast visualization: Generates interactive HTML to review annotated results, great for verification demos 
ADaSci
+3
Google Developers Blog
+3
Reddit
+3
.

Flexible LLM support: Works seamlessly with Gemini or open‑source models like Ollama, configurable via backends 
jonathansoma.com
+5
Google Developers Blog
+5
GitHub
+5
.

How I Used It
python
Copy
Edit
import textwrap
import langextract as lx

prompt = textwrap.dedent("""\
Extract company name, financial metrics, and market sentiment.
Use exact text only. Do not paraphrase.
Provide useful attributes:
- company → include ticker
- metric → type and value
- sentiment → bullish / bearish / neutral
""")

examples = [
  lx.data.ExampleData(
    text="AlphaTech (AT) announced a quarterly profit of $2.5 billion… strongly bullish trend",
    extractions=[
      lx.data.Extraction("company", "AlphaTech", {"stock_ticker":"AT"}),
      lx.data.Extraction("financial_metric","quarterly profit of $2.5 billion",{"metric_type":"profit","value":"$2.5 billion"}),
      lx.data.Extraction("market_sentiment","strongly bullish trend",{"sentiment":"bullish"})
    ]
  )
]

result = lx.extract(
  text_or_documents="Global Dynamics Inc. (GDI) reported quarterly revenue of $15B… stock dipped 2%, cautious sentiment.",
  prompt_description=prompt,
  examples=examples,
  model_id="gemini‑2.5‑pro"
)
That returned perfectly structured JSON along with source offsets—and you can immediately view it in an HTML visualizer.

TL;DR Summary
Benefit	Why It Matters
Traceable output	See where every piece of data was extracted
Schema guarantees	Prompt‑based structure ensures consistent output
Scalable to long docs	Chunking + multi‑pass improves recall
Domain‑agnostic	Works equally well for finance, healthcare, legal, etc.
