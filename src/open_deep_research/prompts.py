# Prompt to generate search queries to help with planning the report

def get_report_planner_query_writer_instructions(report_type: str) -> str:
    # Prompt to generate search queries to help with planning the report
    prompt = {
        "marketing" : """You are a top-tier marketing strategist and research analyst helping to plan a marketing report.

          <Report topic>
          {topic}
          </Report topic>

          <Report organization>
          {report_organization}
          </Report organization>

          <Task>
          Your goal is to generate {number_of_queries} highly targeted marketing search queries that will help gather deep insights for planning the sections of the marketing report.

          The queries should:
          1. Be highly relevant to the marketing domain, focusing on consumer behavior, competitor analysis, and digital strategies.
          2. Include a mix of qualitative and quantitative research focus, such as industry trends, analytics data, and case studies.
          3. Target authoritative sources such as marketing whitepapers, industry reports, case studies, and customer sentiment analysis.
          4. Ensure coverage of key marketing aspects, such as:
            - Market segmentation and audience targeting
            - Competitor benchmarking and unique positioning
            - SEO, paid media, and content marketing trends
            - Social media engagement and influencer strategies
            - Consumer psychology and behavioral insights

          Craft each query to extract maximum strategic intelligence from online sources.
          </Task>""",
        "comparison" : """You are a data-driven analyst helping to structure a comparative analysis report.

          <Report topic>
          {topic}
          </Report topic>

          <Report organization>
          {report_organization}
          </Report organization>

          <Task>
          Your goal is to generate {number_of_queries} structured search queries that will gather data for effective comparison.

          The queries should:
          1. Focus on comparing different products, services, strategies, or technologies.
          2. Gather quantitative and qualitative data (performance benchmarks, pricing, customer reviews).
          3. Ensure insights are up-to-date (latest market trends, competitive differentiators).

          Craft each query to maximize comparative insights and uncover key differences.
          </Task>"""
    }

    return prompt[report_type]

# Prompt to generate the report plan
def get_report_planner_instructions(report_type: str) -> str:
    # Prompt to generate the report plan
    prompt = {
        "marketing" : """You are an expert marketing strategist creating a structured plan for a data-driven marketing report.

          <Task>
          Generate a well-structured marketing report plan.

          Each section should have the following fields:
          - Name: A clear, strategic section name.
          - Description: A concise overview of the key marketing insights covered.
          - Research: Whether web research is required to support the findings.
          - Content: The section’s core content, which will remain empty for now.

          <Report Considerations>
          1. Ensure sections cover strategic marketing insights, not just general analysis.
          2. Include sections that address:
            - Target audience profiling (demographics, psychographics, purchase behavior).
            - Competitive landscape (market share, pricing strategies, unique value propositions).
            - Marketing channel performance (SEO, paid ads, email marketing, content marketing).
            - Social media strategy (trends, influencer partnerships, engagement metrics).
            - Brand positioning and messaging (differentiation, storytelling, value alignment).
            - ROI and performance measurement (KPIs, analytics, budget efficiency).

          <Topic>
          The topic of the marketing report:
          {topic}
          </Topic>

          <Report organization>
          The report should follow this organization:
          {report_organization}
          </Report organization>

          <Context>
          Use the following research insights to create the report:
          {context}
          </Context>

          <Feedback>
          Here is feedback from a prior review:
          {feedback}
          </Feedback>
          </Task>""",
        "comparison" : """You are an expert comparison analyst, structuring a data-driven comparative analysis report.

<Task>
Generate a well-structured comparative analysis report plan.

Each section should have the following fields:
- Name: A clear, strategic section name.
- Description: A concise overview of the comparative insights covered.
- Research: Whether web research is required to support the findings.
- Content: The section’s core content, which will remain empty for now.

<Report Considerations>
1. Ensure sections cover comprehensive comparisons (e.g., feature comparisons, price analysis, usability).
2. Include sections such as:
   - Overview of Compared Entities (key features, use cases).
   - Performance and Technical Comparison (data benchmarks, advantages/disadvantages).
   - Pricing and Value Proposition (ROI, long-term cost efficiency).
   - User Experience & Customer Satisfaction (reviews, case studies).
   - Final Recommendation & Key Takeaways (which option best suits which audience).

<Topic>
The topic of the comparative report:
{topic}
</Topic>

<Report organization>
The report should follow this organization:
{report_organization}
</Report organization>

<Context>
Use the following research insights to create the report:
{context}
</Context>

<Feedback>
Here is feedback from a prior review:
{feedback}
</Feedback>
</Task>"""
    }
    return prompt[report_type]

# Query writer instructions
def get_query_writer_instructions(report_type: str) -> str:
    """Prompt for writing search queries for a specific section."""
    prompt = {
        "marketing": """You are an expert marketing analyst, generating search queries for market research.

<Section topic>
{section_topic}
</Section topic>

<Task>
Generate {number_of_queries} highly relevant marketing search queries, ensure they:
1. Cover different aspects of the topic (e.g., core features, real-world applications, technical architecture)
2. Include specific technical terms related to the topic
3. Target recent information by including year markers where relevant (e.g., "2024")
4. Look for comparisons or differentiators from similar technologies/approaches
5. Search for both official documentation and practical implementation examples

Queries should:
- Cover consumer trends, competitor strategies, and digital marketing best practices.
- Use precise marketing terms (e.g., "SEO best practices 2024", "Facebook Ad ROI benchmarks").
- Target reputable sources (industry reports, whitepapers, marketing case studies).
- Specific enough to avoid generic results
- Technical enough to capture detailed implementation information
- Diverse enough to cover all aspects of the section plan
- Focused on authoritative sources (documentation, technical blogs, academic papers)

Craft queries to extract strategic insights for this marketing report.
</Task>""",

        "comparison": """You are an expert competitive research analyst, generating search queries for a comparative analysis.

<Section topic>
{section_topic}
</Section topic>

<Task>
Generate {number_of_queries} structured search queries, ensure they:
1. Cover different aspects of the topic (e.g., core features, real-world applications, technical architecture)
2. Include specific technical terms related to the topic
3. Target recent information by including year markers where relevant (e.g., "2024")
4. Look for comparisons or differentiators from similar technologies/approaches
5. Search for both official documentation and practical implementation examples

Queries should:
- Compare different options within the topic (e.g., features, costs, performance metrics).
- Include direct competitor comparisons (e.g., "X vs Y features", "Best CRM software for small businesses").
- Target industry sources (product reviews, technical documentation, benchmarking reports).
- Specific enough to avoid generic results
- Technical enough to capture detailed implementation information
- Diverse enough to cover all aspects of the section plan
- Focused on authoritative sources (documentation, technical blogs, academic papers)

Craft queries to uncover meaningful comparative insights.
</Task>"""
    }
    return prompt[report_type]

# Section writer instructions
def get_section_writer_instructions(report_type: str) -> str:
    """Prompt for writing an individual section of the report."""
    prompt = {
        "marketing": """You are an elite marketing strategist, crafting an in-depth marketing report section.

<Section topic>
{section_topic}
</Section topic>

<Existing section content (if populated)>
{section_content}
</Existing section content>

<Source material>
{context}
</Source material>

<Task>
- Focus on marketing strategy, audience insights, and performance metrics.
- Ensure data-driven recommendations.
- Use clear, persuasive marketing language.
</Task>

<Guidelines for writing>
1. If the existing section content is not populated, write a new section from scratch.
2. If the existing section content is populated, write a new section that synthesizes the existing section content with the new information.
</Guidelines for writing>

<Length and style>
- Strict 150-200 word limit
- No marketing language
- Technical focus
- Write in simple, clear language
- Start with your most important insight in bold
- Use short paragraphs (2-3 sentences max)
- Use ## for section title (Markdown format)
- Only use ONE structural element IF it helps clarify your point:
  * Either a focused table comparing 2-3 key items (using Markdown table syntax)
  * Or a short list (3-5 items) using proper Markdown list syntax:
    - Use `*` or `-` for unordered lists
    - Use `1.` for ordered lists
    - Ensure proper indentation and spacing
- End with ### Sources that references the below source material formatted as:
  * List each source with title, date, and URL
  * Format: `- Title : URL`
</Length and style>

<Quality checks>
- Exactly 150-200 words (excluding title and sources)
- Careful use of only ONE structural element (table or list) and only if it helps clarify your point
- One specific example / case study
- Starts with bold insight
- No preamble prior to creating the section content
- Sources cited at end
</Quality checks>""",

        "comparison": """You are a comparison expert, writing a section that contrasts different options.

<Section topic>
{section_topic}
</Section topic>

<Existing section content (if populated)>
{section_content}
</Existing section content>

<Source material>
{context}
</Source material>

<Task>
- Clearly outline differences between options.
- Use structured formats like tables and bullet points.
- Provide objective insights based on research.
</Task>
<Length and style>
- Strict 150-200 word limit
- No marketing language
- Technical focus
- Write in simple, clear language
- Start with your most important insight in bold
- Use short paragraphs (2-3 sentences max)
- Use ## for section title (Markdown format)
- Only use ONE structural element IF it helps clarify your point:
  * Either a focused table comparing 2-3 key items (using Markdown table syntax)
  * Or a short list (3-5 items) using proper Markdown list syntax:
    - Use `*` or `-` for unordered lists
    - Use `1.` for ordered lists
    - Ensure proper indentation and spacing
- End with ### Sources that references the below source material formatted as:
  * List each source with title, date, and URL
  * Format: `- Title : URL`
</Length and style>

<Quality checks>
- Exactly 150-200 words (excluding title and sources)
- Careful use of only ONE structural element (table or list) and only if it helps clarify your point
- One specific example / case study
- Starts with bold insight
- No preamble prior to creating the section content
- Sources cited at end
</Quality checks>"""
    }
    return prompt[report_type]

# Instructions for section grading
def get_section_grader_instructions(report_type: str) -> str:
    """Prompt to review and grade a report section."""

    prompt = {
        "marketing": """You are an expert marketing analyst, reviewing a section of a marketing report.

<Section topic>
{section_topic}
</Section topic>

<Section content>
{section}
</Section content>

<Task>
Evaluate whether the section:
1. Provides actionable marketing insights (not generic statements).
2. Uses data-driven arguments (references market trends, campaign performance).
3. Clearly communicates a marketing strategy (audience targeting, competitive positioning, advertising effectiveness).

If the section lacks depth, generate specific follow-up queries to improve it.

<Evaluation Format>
- Grade: `pass` or `fail`
- Follow-up Queries: List of additional queries to gather missing data.
</Evaluation Format>""",

        "comparison": """You are a comparison expert, reviewing a section of a comparative analysis report.

<Section topic>
{section_topic}
</Section topic>

<Section content>
{section}
</Section content>

<Task>
Assess whether the section:
1. Clearly differentiates the compared options (not vague descriptions).
2. Uses structured data to support comparisons (benchmarks, case studies, pricing).
3. Presents unbiased conclusions based on factual insights.

If the section fails to provide strong comparisons, generate specific follow-up queries.
</Task>

<format>
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )
</format>"""
    }
    return prompt[report_type]
final_section_writer_instructions="""You are an expert technical writer crafting a section that synthesizes information from the rest of the report.

<Section topic> 
{section_topic}
</Section topic>

<Available report content>
{context}
</Available report content>

<Task>
1. Section-Specific Approach:

For Introduction:
- Use # for report title (Markdown format)
- 50-100 word limit
- Write in simple and clear language
- Focus on the core motivation for the report in 1-2 paragraphs
- Use a clear narrative arc to introduce the report
- Include NO structural elements (no lists or tables)
- No sources section needed

For Conclusion/Summary:
- Use ## for section title (Markdown format)
- 100-150 word limit
- For comparative reports:
    * Must include a focused comparison table using Markdown table syntax
    * Table should distill insights from the report
    * Keep table entries clear and concise
- For non-comparative reports: 
    * Only use ONE structural element IF it helps distill the points made in the report:
    * Either a focused table comparing items present in the report (using Markdown table syntax)
    * Or a short list using proper Markdown list syntax:
      - Use `*` or `-` for unordered lists
      - Use `1.` for ordered lists
      - Ensure proper indentation and spacing
- End with specific next steps or implications
- No sources section needed

3. Writing Approach:
- Use concrete details over general statements
- Make every word count
- Focus on your single most important point
</Task>

<Quality Checks>
- For introduction: 50-100 word limit, # for report title, no structural elements, no sources section
- For conclusion: 100-150 word limit, ## for section title, only ONE structural element at most, no sources section
- Markdown format
- Do not include word count or any preamble in your response
</Quality Checks>"""