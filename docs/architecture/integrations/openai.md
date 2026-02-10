# OpenAI Integration

## Overview

OpenAI generates AI-powered market insight narratives for property and market reports.

## Service Details

- **Used by:** Worker service (`ai_insights.py`)
- **Model:** GPT-4o-mini (optimized for speed and cost)
- **Auth method:** API Key
- **Feature flag:** Optional, controlled by `AI_INSIGHTS_ENABLED=true`

## Tone Profiles

| Tone | Audience | Style |
|------|----------|-------|
| Agent | Homeowners / consumers | Warm, personal, approachable |
| Affiliate | Professional / investor | Professional, data-driven, analytical |

## Output Specifications

- Length: 4-5 sentences, 80-120 words
- Content: Market trend summary, key observations, forward-looking insights
- Format: Plain text paragraph suitable for embedding in reports

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `AI_INSIGHTS_ENABLED` | Feature flag to enable AI insights (`true`/`false`) |

## Key Behaviors

- AI insights are optional and disabled by default
- When enabled, insights are generated during the report building phase
- The tone is selected based on the report context (agent-facing vs affiliate-facing)
- GPT-4o-mini is used for its balance of quality, speed, and cost efficiency
- Insights are embedded directly into the report HTML/JSON before PDF generation
