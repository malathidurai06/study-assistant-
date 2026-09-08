"""
tools.py
---------
Specialized AI Tools for Study Assistant:
1. generate_quiz(topic, context, num_questions) -> formatted quiz with answers & explanations
2. generate_study_plan(topics, days) -> day-by-day interactive roadmap with tasks
3. generate_flashcards(topic, context, count) -> high-yield Q&A flashcards
"""

from llm_client import call_llm


def generate_quiz(topic: str, context: str = "", num_questions: int = 5) -> str:
    system_prompt = (
        "You are an expert exam creator and tutor. Create engaging, high-quality multiple-choice "
        "questions on the given topic. Use the course context when available, but use expert knowledge "
        "if context is minimal. Format each question clearly with markdown:\n\n"
        "### Question X: [Question text]\n"
        "- **A)** [Option A]\n"
        "- **B)** [Option B]\n"
        "- **C)** [Option C]\n"
        "- **D)** [Option D]\n\n"
        "<details>\n<summary>🔍 <b>Show Correct Answer & Explanation</b></summary>\n\n"
        "**Correct Answer:** [A/B/C/D]\n\n"
        "**Explanation:** [Brief 1-2 sentence why this is correct and why other options are wrong]\n"
        "</details>\n"
    )
    user_prompt = (
        f"Topic: {topic}\n"
        f"Course context:\n{context or 'No specific context provided; generate from comprehensive topic knowledge.'}\n\n"
        f"Generate {num_questions} conceptual and practical questions."
    )
    return call_llm(system_prompt, [{"role": "user", "content": user_prompt}], max_tokens=1500)


def generate_study_plan(topics: list, days: int = 5) -> str:
    system_prompt = (
        "You are an elite academic mentor and study strategist. Design a highly effective, "
        "motivating day-by-day study roadmap based on the student's explored topics. "
        "Use formatted markdown with daily milestones, estimated time commitments, actionable checklist items (- [ ]), "
        "and key practice prompts."
    )
    topics_str = ", ".join(topics) if topics else "Fundamental Computer Science & Problem Solving"
    user_prompt = (
        f"Topics to master: {topics_str}\n"
        f"Target Timeline: {days} Days\n\n"
        "Structure the plan with:\n"
        "1. 🎯 Overall Goal & Strategy\n"
        "2. 📅 Daily Breakdown (Day 1 to Day N) with - [ ] task checkboxes\n"
        "3. 💡 High-Yield Exam / Interview Tips"
    )
    return call_llm(system_prompt, [{"role": "user", "content": user_prompt}], max_tokens=1500)


def generate_flashcards(topic: str, context: str = "", count: int = 5) -> str:
    system_prompt = (
        "You are a memory and active-recall specialist. Create high-yield revision flashcards "
        "for the student. Format each flashcard as:\n\n"
        "### 📇 Flashcard X: [Front / Key Term / Core Question]\n"
        "<details>\n<summary>💡 <b>Reveal Back / Answer</b></summary>\n\n"
        "[Concise, bulleted answer + mnemonic or quick trick to remember]\n"
        "</details>\n"
    )
    user_prompt = (
        f"Topic: {topic}\n"
        f"Context:\n{context or 'Use comprehensive knowledge'}\n\n"
        f"Create {count} essential flashcards."
    )
    return call_llm(system_prompt, [{"role": "user", "content": user_prompt}], max_tokens=1200)
