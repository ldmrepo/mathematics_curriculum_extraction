# OpenAI GPT Models Available via API (August 2025)

## Currently Available Models

Based on research as of August 2025, the following OpenAI models are available via API:

### GPT-5 Series (NEW - August 2025)
1. **gpt-5** ⭐ LATEST
   - Model name: `gpt-5`
   - Context: 200K tokens
   - Best for: Most advanced reasoning, 45% fewer factual errors with web search
   - Features: Significantly smarter across the board
   - Pricing: TBD (Premium tier)

### GPT-4.1 Series (NEW - 2025)
1. **gpt-4.1** ⭐ RECOMMENDED
   - Model name: `gpt-4.1`
   - Context: 1M tokens (1 million!)
   - Knowledge cutoff: June 2024
   - Best for: Complex coding, instruction following
   - Performance: 21.4% better than GPT-4o on SWE-bench
   - Pricing: Lower cost than GPT-4o

2. **gpt-4.1-mini**
   - Model name: `gpt-4.1-mini`
   - Context: 1M tokens
   - Best for: Fast, efficient tasks
   - Pricing: Budget-friendly

3. **gpt-4.1-nano**
   - Model name: `gpt-4.1-nano`
   - Context: 1M tokens
   - Best for: High-volume, simple tasks
   - Pricing: Most cost-effective

### O-Series Reasoning Models (NEW)
1. **o3** ⭐ Advanced Reasoning
   - Model name: `o3`
   - Best for: Complex reasoning tasks
   - Features: Latest reasoning capabilities

2. **o4-mini** 
   - Model name: `o4-mini`
   - Best for: Fast, cost-efficient reasoning
   - Performance: Best on AIME 2024 and 2025
   - Specialties: Math, coding, visual tasks

### GPT-4o Series (Still Available)
1. **gpt-4o**
   - Model name: `gpt-4o`
   - Context: 128K tokens
   - Best for: Multimodal tasks (text & vision)
   - Note: Being superseded by GPT-4.1
   - Pricing: ~$2.50/1M input tokens, ~$10/1M output tokens

2. **gpt-4o-mini**
   - Model name: `gpt-4o-mini`
   - Context: 128K tokens
   - Best for: Legacy applications
   - Note: Consider upgrading to gpt-4.1-mini
   - Pricing: ~$0.15/1M input tokens, ~$0.60/1M output tokens

### GPT-3.5 Series
1. **gpt-3.5-turbo**
   - Model name: `gpt-3.5-turbo` or `gpt-3.5-turbo-0125`
   - Context: 16K tokens
   - Best for: Simple tasks, high speed
   - Pricing: ~$0.50/1M input tokens, ~$1.50/1M output tokens

## Important Notes

1. **GPT-5 Status**: ✅ GPT-5 has been RELEASED as of August 2025!

2. **Model Selection Recommendations (Updated August 2025)**:
   - For most advanced reasoning: `gpt-5`
   - For complex tasks with huge context: `gpt-4.1` (1M tokens!)
   - For balanced cost/performance: `gpt-4.1-mini`
   - For high-volume, simple tasks: `gpt-4.1-nano`
   - For mathematical reasoning: `o4-mini`
   - For legacy support: `gpt-4o`

3. **API Configuration**:
   ```python
   # Recommended configuration for project (August 2025)
   "gpt5": {
       "name": "gpt-5",
       "max_tokens": 8192,
       "temperature": 0.1
   }
   
   "gpt4_1": {
       "name": "gpt-4.1",
       "max_tokens": 4096,
       "temperature": 0.2
   }
   
   "gpt4_1_mini": {
       "name": "gpt-4.1-mini",
       "max_tokens": 4096,
       "temperature": 0.3
   }
   
   "o4_mini": {
       "name": "o4-mini",
       "max_tokens": 4096,
       "temperature": 0.1
   }
   ```

4. **Cost Optimization**:
   - Use Batch API for 50% cost reduction on non-urgent tasks
   - Consider `gpt-4o-mini` for high-volume, simple operations
   - Implement caching for repeated queries

5. **Context Window Sizes**:
   - 128K tokens: gpt-4-turbo, gpt-4o, gpt-4o-mini
   - 32K tokens: gpt-4-32k
   - 16K tokens: gpt-3.5-turbo
   - 8K tokens: gpt-4

## Deprecation Notice

**GPT-4.5 Preview** will be deprecated on July 14, 2025. Migrate to GPT-4.1.

## Migration Recommendations

For projects using older models:
- `gpt-4-turbo` → `gpt-4.1`
- `gpt-4o` → `gpt-4.1` or `gpt-5`
- `gpt-4o-mini` → `gpt-4.1-mini`
- `gpt-3.5-turbo` → `gpt-4.1-nano`

---
*Last updated: August 2025*
*Source: OpenAI API Documentation and Pricing*