import json
import re
import logging
import requests
import google.generativeai as genai

logging.basicConfig(
    filename="karbon_ai_errors.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

ai_status = {"state": "connecting", "message": "Connecting to AI service..."}


def set_ai_status(state: str, message: str):
    ai_status["state"] = state
    ai_status["message"] = message
    logging.info(f"AI Status Updated: {state} - {message}")


def extract_json(response: str) -> dict:
    clean_response = response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[len("```json"):].strip()
    if clean_response.endswith("```"):
        clean_response = clean_response[:-len("```")].strip()

    try:
        parsed_json = json.loads(clean_response)
        return parsed_json
    except json.JSONDecodeError as e:
        logging.error(f"JSONDecodeError on cleaned string: {e} - Cleaned: {clean_response}")

        match = re.search(r'\{.*\}', clean_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e_inner:
                logging.error(f"JSONDecodeError during regex extraction: {e_inner} - Substring: {match.group(0)}")
                return None
        logging.error(f"No valid JSON object found in response after cleaning: {response}")
        return None


def generate_code_from_prompt(prompt: str, api_key: str = None, model_source: str = None, retries=2) -> str:
    formatted = (
        f"You are a helpful assistant that writes complete frontend apps.\n"
        f"Given the task: \"{prompt}\"\n"
        f"Respond ONLY in this JSON format, with no additional text, markdown, or explanation before or after the JSON:\n"
        "{\n"
        "  \"html\": \"<html>...</html>\",\n"
        "  \"css\": \"body { ... }\",\n"
        "  \"js\": \"document.addEventListener(...)\",\n"
        "  \"name\": \"App Name\"\n"
        "}"
    )
    last_exception = None
    try:
        set_ai_status("connecting", "Connecting to AI service...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        set_ai_status("error", f"AI service unavailable (no internet connection or invalid API key).")
        logging.error(f"Generative AI init failed: {e}")
        return "<!DOCTYPE html><html><head><title>Error</title><style></style></head><body><h1>AI service is currently unavailable.</h1></body></html>"

    for attempt in range(retries + 1):
        try:
            set_ai_status("generating", "Generating code...")
            response_obj = model.generate_content(formatted)
            response = response_obj.text

            logging.info(f"Raw AI response: {response}")

            parsed = extract_json(response)

            logging.info(f"Parsed JSON: {parsed}")

            if not parsed:
                set_ai_status("error", "Could not parse AI response.")
                return "<!DOCTYPE html><html><head><title>Error</title><style></style></head><body><h1>Could not parse AI response.</h1><script></script></body></html>"
            set_ai_status("online", "AI service is online.")
            html = parsed.get("html", "")
            css = parsed.get("css", "")
            js = parsed.get("js", "")

            final_code = html.replace("</head>", f"<style>{css}</style></head>").replace("</body>",
                                                                                         f"<script>{js}</script></body>")

            logging.info(f"Final inlined HTML code (first 500 chars): {final_code[:500]}...")

            return final_code
        except requests.exceptions.RequestException as e:
            last_exception = e
            set_ai_status("offline", "Network error, AI service is offline.")
            logging.error(f"AI API network error: {e}")
        except Exception as e:
            last_exception = e
            set_ai_status("error", f"AI service error: {e}")
            logging.error(f"AI API error: {e}")
        import time
        time.sleep(2 ** attempt)
    set_ai_status("offline", f"AI service unavailable: {last_exception}.")
    return "<!DOCTYPE html><html><head><title>Error</title><style></style></head><body><h1>AI service is currently unavailable.</h1></body></html>"


def optimize_prompt(prompt: str, api_key: str = None) -> str:
    print("[optimize_prompt] Called with:", prompt)

    if len(prompt.strip()) >= 20 and not is_generic(prompt):
        return prompt

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        enriched_response_obj = model.generate_content(
            f"Transform the following vague or minimal UI prompt into a clear, detailed, and professional instruction specifically for frontend web development. "
            f"Focus on HTML, CSS, and JavaScript. Include layout details, components to be included, styling considerations, and any interactivity if relevant. "
            f"Keep the improved prompt concise yet specific. Do not add commentary or formatting:\n\n"
            f"User Prompt: \"{prompt.strip()}\"\n\n"
            f"Refined Prompt:"
        )

        improved = enriched_response_obj.text.strip()
        if not improved:
            print("[optimize_prompt] Empty response, fallback to rule-based enhancement")
            return rule_based_enhancement(prompt)
        return improved

    except Exception as e:
        print(f"[optimize_prompt] Exception: {e}")
        logging.error(f"LLM optimization failed: {e}")
        return rule_based_enhancement(prompt)


def rule_based_enhancement(prompt: str) -> str:
    prompt = prompt.strip()
    modifiers = [
        "Use semantic HTML5 structure.",
        "Apply responsive CSS (mobile-first).",
        "Include clean modular JavaScript with comments."
    ]
    return f"{prompt}\n\n" + "\n".join(modifiers)


def is_generic(prompt: str) -> bool:
    generic_phrases = {
        "make a website", "build ui", "create page", "webpage", "dashboard", "login", "landing page"
    }
    return prompt.lower().strip() in generic_phrases