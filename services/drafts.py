def build_draft_text(microcategory, matched_phrases):
    title = microcategory["mcTitle"]
    phrases = matched_phrases[:3]

    if phrases:
        phrase_text = ", ".join(phrases)
        return f"Выполняем услуги по направлению '{title}'. Возможны работы: {phrase_text}."

    return f"Выполняем работы по направлению '{title}'. Подробности и состав услуг уточняются."


def build_drafts(split_candidates):
    drafts = []

    for candidate in split_candidates:
        drafts.append(
            {
                "mcId": candidate["mcId"],
                "mcTitle": candidate["mcTitle"],
                "text": build_draft_text(candidate, candidate["matchedPhrases"]),
            }
        )

    return drafts
