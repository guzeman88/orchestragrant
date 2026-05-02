from __future__ import annotations

from typing import Optional


def build_section_prompt(
    section_title: str,
    section_prompt: Optional[str],
    grant_title: Optional[str],
    grant_description: Optional[str],
    requested_amount: Optional[float],
    word_limit: Optional[int],
    tone: str,
    atoms: list[dict],
    existing_content: Optional[str],
) -> str:
    tone_instructions = {
        "professional": "Write in a polished, formal tone appropriate for institutional funders.",
        "warm": "Write in a warm, personal tone that conveys genuine passion for the mission.",
        "urgent": "Write with a sense of urgency about community need and organizational impact.",
        "data_driven": "Lead with data and measurable outcomes. Be concrete and specific.",
    }

    tone_instr = tone_instructions.get(tone, tone_instructions["professional"])

    sources_block = "\n\n".join(
        f"[Source {i+1}] {atom['text']}" for i, atom in enumerate(atoms)
    ) if atoms else "No source documents available."

    word_instr = f"Keep the response under {word_limit} words." if word_limit else ""

    existing_block = (
        f"\n\nExisting draft (revise and improve this):\n{existing_content}"
        if existing_content
        else ""
    )

    return f"""You are writing a grant application section for a performing arts organization.

## Section to Write
Title: {section_title}
{f'Instructions: {section_prompt}' if section_prompt else ''}

## Grant Context
{f'Grant: {grant_title}' if grant_title else ''}
{f'Grant Description: {grant_description}' if grant_description else ''}
{f'Amount Requested: ${requested_amount:,.0f}' if requested_amount else ''}

## Tone Guidance
{tone_instr}
{word_instr}

## Source Material (use ONLY information from these sources)
{sources_block}
{existing_block}

Write the section now. Ground every claim in the source material above. Do not add any information not present in the sources.
"""
