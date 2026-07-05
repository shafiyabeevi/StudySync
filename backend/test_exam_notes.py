import asyncio
import traceback
from app.services.notes_generator import generate_exam_notes


async def main() -> None:
    try:
        result = await generate_exam_notes(
            'This is a test document about photosynthesis and mitosis. Key terms: ATP, chlorophyll. Important formula: E = mc^2',
            'sample.pdf',
        )
        print(type(result).__name__)
        print(result)
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
