"""
Simple Skills Demo

Quick demonstration of the skills framework basics.
"""

import asyncio
import sys
import io

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ai.skills import (
    SkillRegistry,
    SkillExecutor,
    SkillChain,
    SkillContext
)
from ai.skills.example_skills import (
    TextAnalyzerSkill,
    MathCalculatorSkill,
    TextSummarizerSkill
)


async def main():
    print("=" * 50)
    print("Simple Skills Framework Demo")
    print("=" * 50)

    # 1. Setup
    print("\n1. Setting up registry and executor...")
    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # 2. Register skills
    print("2. Registering skills...")
    registry.register(TextAnalyzerSkill())
    registry.register(MathCalculatorSkill())
    registry.register(TextSummarizerSkill())

    print(f"   ✓ Registered {len(registry)} skills")

    # 3. Execute a simple skill
    print("\n3. Analyzing text...")
    result = await executor.execute(
        "text_analyzer",
        text="Artificial intelligence is revolutionizing technology. "
             "Machine learning enables computers to learn from data."
    )

    if result.success:
        print(f"   ✓ Words: {result.data['word_count']}")
        print(f"   ✓ Sentences: {result.data['sentence_count']}")
        print(f"   ✓ Top words: {result.data['top_words'][:3]}")

    # 4. Execute calculation
    print("\n4. Performing calculation...")
    result = await executor.execute(
        "math_calculator",
        expression="(100 + 50) * 2"
    )

    if result.success:
        print(f"   ✓ {result.data['expression']} = {result.data['result']}")

    # 5. Create a chain
    print("\n5. Creating a skill chain...")
    chain = SkillChain(executor, "AnalysisChain")

    chain.add_step(
        "text_analyzer",
        parameters={"text": "The quick brown fox jumps over the lazy dog. "
                            "This sentence contains every letter of the alphabet."}
    )

    chain.add_step(
        "text_summarizer",
        transform_input=lambda data: {
            "text": f"Analysis: {data['word_count']} words, "
                    f"{data['sentence_count']} sentences",
            "max_length": 50
        }
    )

    print("   Executing chain...")
    result = await chain.execute()

    if result.success:
        print(f"   ✓ Chain completed in {result.execution_time:.3f}s")
        print(f"   ✓ Final result: {result.data}")

    # 6. Show statistics
    print("\n6. Statistics:")
    stats = executor.get_statistics()
    print(f"   - Total executions: {stats['total_executions']}")
    print(f"   - Success rate: {stats['success_rate']:.1%}")

    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
