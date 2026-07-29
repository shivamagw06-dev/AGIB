# AGIB v4.0 — AI-Native Institutional Research Workspace

`/ask` is no longer a research-note dashboard. It is a **conversation with a CIO**.

## Experience

1. **Direct answer** — institutional view, horizon, confidence  
2. **Investment Thesis** — expandable cards (business, growth, financials, valuation, competition, risk, catalysts)  
3. **What Would Change AGIB's View?** — more bullish / more bearish  
4. **Supporting Intelligence** — clickable chips that reveal evidence layers  
5. **Follow-ups** — continue the conversation  
6. **Right rail** — conviction scores, refresh, recent research  

## Files

| Piece | Path |
| --- | --- |
| Page | `src/pages/AskAgiPage.jsx` |
| Workspace | `src/components/AskAgi/InstitutionalChatWorkspace.jsx` |
| Styles | `src/components/AskAgi/institutionalChat.css` |
| Chat adapter | `src/components/AskAgi/adapters/mapChatAnswer.js` |
| Pack mapper (reuse) | `src/components/AskAgi/adapters/mapSearchPack.js` |

Legacy `ResearchWorkspace.jsx` remains in the repo but is not mounted on `/ask`.

## Design tokens

- Dark navy sidebar (`#0b1f33`)
- White / soft canvas conversation
- Deep blue primary, institutional green, amber warning, muted red
- Source Serif 4 + IBM Plex Sans
- No neon, glassmorphism, or crypto aesthetics
