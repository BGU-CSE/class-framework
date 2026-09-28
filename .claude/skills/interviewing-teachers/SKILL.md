---
name: interviewing-teachers
description: How to interview a teacher without wasting their time on things you already know. Use whenever an agent asks the teacher a follow-up question — during ingest, planning, item writing, or when proposing a new entry to course.yaml.
---

# Interviewing teachers

Teachers are experts in *their course*. They are not experts in defining public concepts to
you, and they will resent being asked to. If you are about to ask what something is when you
could look it up, stop.

## The move

Draft what you would write. Show it. Ask the teacher only about the course-specific facts you
genuinely cannot know.

| Bad question | Good question |
|---|---|
| "What is Wireshark?" | "Wireshark isn't in course.yaml yet. I'd add: `description: Network protocol analyzer for capturing and inspecting packets.` and `availability: student_download`. Correct?" |
| "What does CLRS stand for?" | "Adding CLRS as `Cormen, Leiserson, Rivest, Stein — Introduction to Algorithms, 4th ed.` — is that the edition your course uses?" |
| "How much time do students spend on this?" | "I'd estimate 20 minutes for this session based on the reading length. Does that match what you've seen in past semesters?" |
| "What's the prerequisite here?" | "This session assumes recursion (U02). Is that the right prerequisite, or does it also need induction from the discrete math course?" |

The pattern is the same in every row: you draft, then you ask about the specific thing you
couldn't have known.

## What to ask about

- **Availability, versioning, access.** Whether students have this tool installed, which version
  the course requires, whether the textbook is in the library, whether the dataset is on the
  department server.
- **House style and voice.** How this teacher describes something to their students. Your draft
  is neutral; theirs might be sharper or warmer.
- **Local pedagogical choices.** Which of two equivalent framings this course prefers. Whether
  this concept is taught before or after that one. What's out of scope this semester.
- **Facts you couldn't verify from what's public.** Whether the teacher has seen students
  struggle with a specific misconception. Which textbook chapter they actually cover.

## What to never ask about

- **Definitions of public terms.** What Wireshark is. What CLRS stands for. What "amortized
  analysis" means. Look it up.
- **Standard curriculum shape.** Whether a data structures course usually covers hash tables.
  Whether a networking course usually covers TCP. Draft the assumption, let them correct.
- **Your own reasoning.** "Do you want me to make sure the items map to guiding questions?"
  You know the answer. Do it and mention it in your report.

## Failure modes

**The definition trap.** Asking "what is X?" for anything with a Wikipedia page. Draft from
what you know; if the teacher's use of the term differs from the canonical one, they'll say
so when they see the draft.

**The teach-me trap.** Framing follow-ups as if the teacher owes you an explanation. "Could
you tell me more about how you use Wireshark?" is worse than "Here's how I imagine a Wireshark
homework works — captures are collected in the lab, students annotate them. Does that match?"

**The blank-slate trap.** Pretending you have no priors. "What kind of homework do you usually
give?" is worse than "I'd propose 3 open questions plus one coding item, ~60 minutes total.
Adjust?"

**The interview-as-checklist trap.** Asking every question you *could* ask because you have a
list. Every question the teacher answers is a question that should have been necessary. If
the answer barely changes what you'd do, don't ask.

## Phrasing

Show your draft in the same message as the question. The teacher confirms with "yes" or corrects
in one line. Never make them type out what you could have typed for them.

Prefer "I'd write X — correct?" over "How should I write this?". The first invites a
one-word yes or a targeted edit; the second invites a paragraph.

When you genuinely don't know something, say so plainly and specifically. "I don't know how
your course handles late submissions" is fine. "Tell me about your course" is not.
