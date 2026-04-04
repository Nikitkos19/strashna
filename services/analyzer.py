import re

from services.drafts import build_drafts

TOKEN_PATTERN = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)
SENTENCE_SPLIT_PATTERN = re.compile(r"[.!?;\n]+")
TURNKEY_REPAIR_PATTERN = re.compile(
    r"(ремонт\w*|отделк\w*|обновлен\w*)[^,.!?\n]{0,30}под ключ|под ключ[^,.!?\n]{0,30}(ремонт\w*|отделк\w*|обновлен\w*)"
)
STOP_WORDS = {
    "и",
    "а",
    "но",
    "или",
    "для",
    "под",
    "над",
    "по",
    "на",
    "в",
    "во",
    "с",
    "со",
    "к",
    "ко",
    "от",
    "до",
    "из",
    "у",
    "за",
    "без",
    "при",
}
COMMON_ENDINGS = (
    "иями",
    "ями",
    "ами",
    "ого",
    "ему",
    "ому",
    "ыми",
    "ими",
    "его",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ый",
    "ий",
    "ой",
    "ым",
    "им",
    "ом",
    "ем",
    "ах",
    "ях",
    "ам",
    "ям",
    "ов",
    "ев",
    "ей",
    "ую",
    "юю",
    "ть",
    "ти",
    "ка",
    "ки",
    "ке",
    "ку",
    "ой",
    "ий",
    "ия",
    "ие",
    "ию",
    "иям",
    "иях",
    "а",
    "я",
    "ы",
    "и",
    "е",
    "у",
    "ю",
    "о",
)
STANDALONE_MARKERS = (
    "отдельно",
    "отдельные",
    "отдельный",
    "отдельная",
    "также",
    "а также",
    "кроме того",
    "дополнительно",
    "самостоятельно",
)
SERVICE_VERBS = (
    "выполняем",
    "делаем",
    "оказываем",
    "предлагаем",
    "берем",
    "монтируем",
    "устанавливаем",
)
BUNDLED_MARKERS = (
    "включая",
    "в составе",
    "в рамках",
    "входит",
    "все этапы",
    "под ключ",
    "комплекс",
    "комплексный",
)
STRICT_MATCH_MC_IDS = {101}
TURNKEY_MARKERS = (
    "под ключ",
    "комплексный ремонт",
    "комплексная отделка",
    "весь цикл ремонта",
    "полный ремонт",
    "полное обновление",
    "ремонт с нуля",
    "ремонт полностью",
    "выполняем весь комплекс работ",
)
REPAIR_CONTEXT_MARKERS = (
    "ремонт под ключ",
    "комплексный ремонт",
    "комплексная отделка",
    "полный ремонт",
    "полное обновление",
    "отделка под ключ",
    "весь цикл ремонта",
    "генподряд",
    "объект целиком",
    "комплекс работ",
)
NO_SPLIT_MARKERS = (
    "по отдельным видам работ не выезжаю",
    "по отдельным работам не выезжаю",
    "ищу заказы именно на комплекс",
    "как часть ремонта",
    "в составе ремонта",
    "выполняем все работы одной бригадой",
    "без дробления на этапы",
    "не делим на этапы",
    "только комплекс",
    "только под ключ",
)
GENERIC_PHRASES_BY_MC = {
    111: {"демонтаж", "разборка"},
}


def normalize_text(text):
    return " ".join(text.lower().split())


def tokenize(text):
    return TOKEN_PATTERN.findall(text.lower())


def stem_token(token):
    token = token.lower().replace("ё", "е")

    for ending in COMMON_ENDINGS:
        if token.endswith(ending) and len(token) - len(ending) >= 4:
            return token[: -len(ending)]

    return token


def phrase_to_stems(phrase):
    stems = []

    for token in tokenize(phrase):
        if token in STOP_WORDS:
            continue
        stems.append(stem_token(token))

    return stems


def build_description_index(description):
    tokens = tokenize(description)
    stems = [stem_token(token) for token in tokens]
    sentences = [
        normalize_text(sentence)
        for sentence in SENTENCE_SPLIT_PATTERN.split(description)
        if normalize_text(sentence)
    ]

    return {
        "normalized": normalize_text(description),
        "tokens": tokens,
        "stem_set": set(stems),
        "sentences": sentences,
    }


def phrase_matches_description(phrase, description_index):
    normalized_phrase = normalize_text(phrase)

    if normalized_phrase and normalized_phrase in description_index["normalized"]:
        return True

    phrase_stems = phrase_to_stems(phrase)
    if not phrase_stems:
        return False

    matched_stems = [
        stem for stem in phrase_stems if stem in description_index["stem_set"]
    ]

    if len(phrase_stems) == 1:
        return bool(matched_stems)

    return len(matched_stems) == len(phrase_stems)


def find_matched_phrases(microcategory, description_index):
    if microcategory["mcId"] == 101:
        return find_turnkey_matches(microcategory, description_index)

    matched_phrases = []

    for phrase in microcategory["keyPhrases"]:
        normalized_phrase = normalize_text(phrase)
        exact_match = (
            bool(normalized_phrase)
            and normalized_phrase in description_index["normalized"]
        )

        if microcategory["mcId"] in STRICT_MATCH_MC_IDS:
            has_turnkey_marker = any(
                marker in description_index["normalized"] for marker in TURNKEY_MARKERS
            )
            if exact_match or (has_turnkey_marker and phrase_matches_description(phrase, description_index)):
                matched_phrases.append(phrase)
            continue

        if exact_match or phrase_matches_description(phrase, description_index):
            matched_phrases.append(phrase)

    generic_phrases = GENERIC_PHRASES_BY_MC.get(microcategory["mcId"], set())
    specific_matches = [
        phrase for phrase in matched_phrases if normalize_text(phrase) not in generic_phrases
    ]
    if generic_phrases and specific_matches:
        return specific_matches

    return matched_phrases


def has_turnkey_repair_context(description_index):
    normalized = description_index["normalized"]
    return any(phrase in normalized for phrase in REPAIR_CONTEXT_MARKERS) or bool(
        TURNKEY_REPAIR_PATTERN.search(normalized)
    )


def find_turnkey_matches(microcategory, description_index):
    exact_matches = []

    for phrase in microcategory["keyPhrases"]:
        normalized_phrase = normalize_text(phrase)
        if normalized_phrase and normalized_phrase in description_index["normalized"]:
            exact_matches.append(phrase)

    if exact_matches:
        return exact_matches

    has_turnkey_marker = any(
        marker in description_index["normalized"] for marker in TURNKEY_MARKERS
    )

    if has_turnkey_marker and has_turnkey_repair_context(description_index):
        return ["ремонт под ключ"]

    return []


def find_detected_microcategories(description, microcategories):
    description_index = build_description_index(description)
    detected = []

    for microcategory in microcategories:
        matched_phrases = find_matched_phrases(microcategory, description_index)

        if matched_phrases:
            detected.append(
                {
                    "mcId": microcategory["mcId"],
                    "mcTitle": microcategory["mcTitle"],
                    "matchedPhrases": matched_phrases,
                    "evidenceSentences": find_evidence_sentences(
                        matched_phrases, description_index["sentences"]
                    ),
                }
            )

    return detected


def should_suppress_detection(microcategory, source_mc_id):
    return False


def apply_detection_overrides(detected_microcategories, source_mc_id):
    return [
        microcategory
        for microcategory in detected_microcategories
        if not should_suppress_detection(microcategory, source_mc_id)
    ]


def find_evidence_sentences(matched_phrases, sentences):
    evidence = []

    for sentence in sentences:
        for phrase in matched_phrases:
            if phrase_matches_description(
                phrase,
                {
                    "normalized": sentence,
                    "tokens": tokenize(sentence),
                    "stem_set": {stem_token(token) for token in tokenize(sentence)},
                    "sentences": [sentence],
                },
            ):
                evidence.append(sentence)
                break

    return evidence


def is_complex_root_category(microcategory):
    title = microcategory["mcTitle"].lower()
    return "под ключ" in title or "комплекс" in title


def score_split_candidate(microcategory):
    standalone_score = 0
    bundled_score = 0

    for sentence in microcategory["evidenceSentences"]:
        has_standalone_marker = any(marker in sentence for marker in STANDALONE_MARKERS)
        has_service_verb = any(verb in sentence for verb in SERVICE_VERBS)
        has_bundled_marker = any(marker in sentence for marker in BUNDLED_MARKERS)

        if has_standalone_marker:
            standalone_score += 2
        if has_service_verb and (has_standalone_marker or not has_bundled_marker):
            standalone_score += 1
        if has_bundled_marker and not has_standalone_marker:
            bundled_score += 2

    if len(microcategory["matchedPhrases"]) >= 2:
        standalone_score += 1

    return standalone_score, bundled_score


def choose_split_candidates(detected_microcategories):
    split_candidates = []

    for microcategory in detected_microcategories:
        if is_complex_root_category(microcategory):
            continue

        standalone_score, bundled_score = score_split_candidate(microcategory)

        if standalone_score > bundled_score:
            split_candidates.append(
                {
                    **microcategory,
                    "standaloneScore": standalone_score,
                    "bundledScore": bundled_score,
                }
            )

    return split_candidates


def has_hard_no_split_signal(description, source_mc_id):
    normalized_description = normalize_text(description)

    if source_mc_id != 101:
        return False

    return any(marker in normalized_description for marker in NO_SPLIT_MARKERS)


def filter_out_source_microcategory(detected_microcategories, source_mc_id):
    if source_mc_id is None:
        return detected_microcategories

    return [
        microcategory
        for microcategory in detected_microcategories
        if microcategory["mcId"] != source_mc_id
    ]


def analyze_ad(description, microcategories, source_mc_id=None):
    detected_microcategories = find_detected_microcategories(description, microcategories)
    detected_microcategories = apply_detection_overrides(
        detected_microcategories,
        source_mc_id,
    )
    additional_microcategories = filter_out_source_microcategory(
        detected_microcategories,
        source_mc_id,
    )
    split_candidates = choose_split_candidates(additional_microcategories)
    if has_hard_no_split_signal(description, source_mc_id):
        split_candidates = []
    drafts = build_drafts(split_candidates)

    return {
        "description": description,
        "sourceMcId": source_mc_id,
        "detectedMcIds": [item["mcId"] for item in detected_microcategories],
        "detectedMcTitles": [item["mcTitle"] for item in detected_microcategories],
        "shouldSplit": bool(split_candidates),
        "drafts": drafts,
    }
