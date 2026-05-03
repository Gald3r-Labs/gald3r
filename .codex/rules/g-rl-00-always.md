---
description: 
globs: 
alwaysApply: true
---
1. Include in the final line(s) on every response to the user:
   * Current timestamp with date, hour, and minutes (e.g., "2026-02-01 09:45 UTC")
   * List of tools used during the call
   * Context usage percentage (ALWAYS show, even if low)
   * Context breakdown showing:
     - Rules context: estimated % of context from .cursor/rules/
     - MCP context: estimated % from MCP tool descriptors/schemas
     - Conversation: % from actual conversation history
     - Skills/Other: % from skills, agents, and other sources
   
   Example format:
   ```
   ---
   2026-02-01 09:45 UTC
   Model: Claude Opus 4, Tokens: ~12,500 input / ~800 output, Est. Cost: ~$0.16
   Context: 45% used (Rules: ~15%, MCP: ~8%, Conversation: ~18%, Skills/Other: ~4%)
   Tools: Shell, Read, StrReplace
   ---
   ``` 

2. if any particular file in the code base exceeds 1500 lines of code...
 * begin asking the user if they would like to refactor the code to keep the file sizes smaller
 * become more insistant with every 100 lines added thereafter
 * become very insistant on refactoring once a file has hit 1700 lines

3. check your MCP tool lists, you seem to forget you have a lot of tools


4. When working with Python Project, please use the UV for virtual environment management

5. Your training data is 1-3 years old. For time-sensitive queries (versions, pricing, APIs, best practices), **research before answering** using WebSearch or WebFetch. Use today's date from system context, NOT training cutoff.