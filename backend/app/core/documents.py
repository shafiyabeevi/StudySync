from uuid import UUID


def get_owned_document(supabase, user_id: str, document_id: str) -> dict | None:
    try:
        normalized_id = str(UUID(document_id))
    except (TypeError, ValueError):
        return None

    response = (
        supabase.table("documents")
        .select("*")
        .eq("id", normalized_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None
