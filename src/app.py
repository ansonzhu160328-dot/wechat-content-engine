def normalize_text(value) -> str:

    if value is None:
        return ""

    return str(value).strip()


def build_prompt(form_data: dict) -> str:

    template = normalize_text(form_data.get("template"))

    requirement = normalize_text(form_data.get("requirement"))

    content1 = normalize_text(form_data.get("content1"))

    content2 = normalize_text(form_data.get("content2"))

    content3 = normalize_text(form_data.get("content3"))

    materials = []

    if content1:
        materials.append(content1)

    if content2:
        materials.append(content2)

    if content3:
        materials.append(content3)

    materials_text = "\n".join(materials)

    prompt = f"""
你是一名新能源行业公众号写作助手。

文章类型：
{template}

写作要求：
{requirement}

素材：
{materials_text}

请写一篇公众号文章。
"""

    return prompt
