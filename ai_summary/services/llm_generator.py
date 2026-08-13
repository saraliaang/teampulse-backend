import os


DEFAULT_MODEL_NAME = "qwen3.7-flash"
DEFAULT_BASE_URL = (
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)
MAX_SUMMARY_WORDS = 80


class LLMGenerationError(Exception):
    """Raised when a team insight cannot be generated safely."""


def build_prompt(metrics):
    return f"""
You are generating a short weekly wellbeing insight for a team manager.

Use only the data provided. Do not invent causes, personal circumstances,
or explanations unsupported by the data. Do not identify individual team
members.

Follow these rules:

- Always begin with: "[X]% completion rate so far this week."
- Interpret average mood using this 1-to-4 scale:
  - Above 3: generally positive
  - From 2 to 3: some concern; suggest a gentle action such as checking in,
    encouraging connection, or creating space for support
  - Below 2: significant concern; explain that the team may need attention
    and suggest a proactive check-in
- Interpret average workload using this 1-to-4 scale:
  - Above 3: generally manageable
  - From 2 to 3: some workload pressure; suggest reviewing priorities,
    redistributing work, or offloading where appropriate
  - Below 2: significant workload concern; recommend actively reviewing
    workload and capacity
- A low workload score means high workload pressure.
- Mention only the number of people needing attention.
- Never identify or speculate about individuals.
- If both metrics are healthy, remain positive without exaggerating.
- If only one area needs attention, clearly distinguish the two areas.
- Keep recommendations practical and appropriate for a manager.
- Do not diagnose mental health conditions.
- Do not use alarmist language.
- Use plain text without headings, bullets, or Markdown.
- Maximum length: {MAX_SUMMARY_WORDS} words.

Example team data:

- Completion rate: 70.0%
- Average mood: 2.6 / 4
- Average workload: 3.7 / 4
- Number of people with low mood: 2
- Number of people with high workload pressure: 1

Example insight:

70% completion rate so far this week. Workload appears generally manageable,
while mood shows some signs of concern. Two people reported low mood, so it
may be worth creating space for a check-in or offering additional support.
Overall capacity looks stable, but team morale may need some attention.

Current team data:

- Completion rate: {metrics["completion_rate"]}%
- Average mood: {metrics["avg_mood"]} / 4
- Average workload: {metrics["avg_workload"]} / 4
- Number of people with low mood: {metrics["low_mood_count"]}
- Number of people with high workload pressure:
  {metrics["low_workload_count"]}

Write one concise weekly team insight following these rules.
""".strip()


def _validate_summary(summary):
    cleaned_summary = " ".join(summary.split())

    if not cleaned_summary:
        raise LLMGenerationError("Qwen returned an empty insight.")

    if len(cleaned_summary.split()) > MAX_SUMMARY_WORDS:
        raise LLMGenerationError(
            f"Qwen returned more than {MAX_SUMMARY_WORDS} words."
        )

    return cleaned_summary


def generate_team_summary(metrics):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMGenerationError(
            "The openai package is not installed."
        ) from exc

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise LLMGenerationError(
            "DASHSCOPE_API_KEY is not configured."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("QWEN_BASE_URL", DEFAULT_BASE_URL),
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You summarize workplace wellbeing metrics accurately, "
                "briefly, and respectfully."
            ),
        },
        {
            "role": "user",
            "content": build_prompt(metrics),
        },
    ]

    try:
        completion = client.chat.completions.create(
            model=os.getenv("QWEN_MODEL", DEFAULT_MODEL_NAME),
            messages=messages,
            max_tokens=160,
            temperature=0.7,
            top_p=0.8,
            extra_body={"enable_thinking": False},
        )
        summary = completion.choices[0].message.content
    except Exception as exc:
        raise LLMGenerationError(
            "Qwen Cloud failed to generate a team insight."
        ) from exc

    return _validate_summary(summary)
