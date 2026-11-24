#!/usr/bin/python3

########################################################################
#                                                                      #
# i18n.py                                                              #
#                                                                      #
# Copyright (C) 2026 maylog                                            #
#                                                                      #
########################################################################

########################################################################
#                                                                      #
# Internationalization (i18n) support for Cubic-Fedora.                #
#                                                                      #
# Translations are stored as PLAIN TEXT files in the                   #
# "cubic/i18n" directory (for example, "cubic/i18n/zh_CN.txt"), one    #
# translation per line, in the following format:                       #
#                                                                      #
#     original text = translated text                                  #
#                                                                      #
# Blank lines and lines starting with "#" are ignored. The escape      #
# sequence "\n" in a key or a value represents a new line character.   #
# The first "=" in a line separates the key from the value.            #
#                                                                      #
# The language is selected using the CUBIC_LANG environment variable   #
# (for example, "CUBIC_LANG=zh_CN"), or the default locale of the      #
# session (for example, "LANG=zh_CN.UTF-8"). If a translation file     #
# for the language does not exist, the original (English) texts are    #
# displayed.                                                           #
#                                                                      #
########################################################################

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import os

########################################################################
# Global Variables & Constants
########################################################################

# The translations for the current language. The keys are the original
# (English) texts, and the values are the translated texts.
translations = {}

# The inverse translations (the translated texts mapped back to the
# original texts). This is used when the display language is switched
# back to the original language.
inverse_translations = {}

# The language that was loaded (for example, "zh_CN"), or None if no
# translation file was loaded.
language = None

# Whether the translations (instead of the original texts) are
# currently displayed.
active = False

# The application directory (stored by initialize(), so that the
# translation file can be loaded later by toggle_language()).
_application_directory = None

########################################################################
# Functions
########################################################################


def initialize(application_directory):
    """
    Load the plain text translation file for the current language. The
    language is selected using the CUBIC_LANG environment variable, or
    the default locale of the session. This function must be invoked
    after the application directory is known, and before the user
    interface is created.

    Arguments:
    application_directory : str
        The directory of the application (which contains the "cubic"
        directory).
    """

    global translations
    global language
    global active
    global _application_directory

    translations = {}
    inverse_translations = {}
    language = None

    # Remember the application directory, so that the translation file
    # can be loaded later by toggle_language().
    _application_directory = application_directory

    # Select the language.
    selected_language = os.environ.get('CUBIC_LANG') or os.environ.get('LC_ALL') or os.environ.get('LANG') or ''
    # Remove the encoding (for example, "zh_CN.UTF-8" becomes "zh_CN").
    selected_language = selected_language.split('.')[0].strip()

    # Load the translation file for the language. Try the full language
    # code first (for example, "zh_CN"), then the language part only
    # (for example, "zh").
    file_paths = []
    if selected_language:
        file_paths.append(os.path.join(application_directory, 'cubic', 'i18n', f'{selected_language}.txt'))
        language_part = selected_language.split('_')[0]
        if language_part and language_part != selected_language:
            file_paths.append(os.path.join(application_directory, 'cubic', 'i18n', f'{language_part}.txt'))

    for file_path in file_paths:
        if os.path.isfile(file_path):
            _load_translation_file(file_path)
            language = os.path.splitext(os.path.basename(file_path))[0]
            break

    # The original (English) texts are displayed by default. The
    # display language is switched to the loaded translations only when
    # the user clicks the language menu item (see toggle_language()).
    active = False

    if language:
        # Avoid a circular import at module load time.
        from cubic.utilities import logger
        logger.log_value('Loaded the translation file for the language', language)
        logger.log_value('The number of translations is', len(translations))


def _load_translation_file(file_path):
    """
    Load a plain text translation file. Each line contains a translation
    in the format "original text = translated text".

    Arguments:
    file_path : str
        The full path of the translation file.
    """

    with open(file_path, encoding='utf-8') as file:
        for line in file:
            line = line.rstrip('\n')
            if not line.strip(): continue
            if line.strip().startswith('#'): continue
            if '=' not in line: continue
            original_text, translated_text = line.split('=', 1)
            original_text = _unescape(original_text.strip())
            translated_text = _unescape(translated_text.strip())
            if original_text:
                translations[original_text] = translated_text


def _unescape(text):
    """
    Convert the escape sequence "\\n" into a new line character.

    Arguments:
    text : str
        The text.

    Returns:
    : str
        The text with escape sequences converted.
    """

    return text.replace('\\n', '\n')


def tr(text):
    """
    Translate the text using the loaded translations. If the text is not
    found in the translations (or no translation file was loaded), the
    text is returned unchanged.

    When the translations are active, the original texts are translated
    into the target language; when the translations are inactive, the
    translated texts are mapped back to the original texts (using the
    inverse translations).

    Arguments:
    text : str
        The text to translate.

    Returns:
    : str
        The translated text, or the original text.
    """

    if not text: return text
    if active:
        return translations.get(str(text), str(text))
    else:
        return inverse_translations.get(str(text), str(text))


def toggle_language():
    """
    Toggle the display language between the original (English) texts and
    the loaded translations. If a translation file was not loaded yet
    (for example, when the session locale is English), the Simplified
    Chinese translation file (zh_CN.txt) is loaded on demand. Returns
    the new display language (for example, "zh_CN" or "en").
    """

    global active
    global inverse_translations
    global language

    # Load the Simplified Chinese translations on demand (when no
    # translation file was loaded, for example when the session locale
    # is English).
    if not translations and _application_directory:
        file_path = os.path.join(_application_directory, 'cubic', 'i18n', 'zh_CN.txt')
        if os.path.isfile(file_path):
            _load_translation_file(file_path)
            language = 'zh_CN'
            # Avoid a circular import at module load time.
            from cubic.utilities import logger
            logger.log_value('Loaded the translation file for the language', language)
            logger.log_value('The number of translations is', len(translations))

    if not translations:
        return 'en'

    # Build the inverse translations (once).
    if not inverse_translations:
        inverse_translations = {value: key for key, value in translations.items()}

    active = not active

    # Avoid a circular import at module load time.
    from cubic.utilities import logger
    logger.log_value('The display language was switched to', current_display_language())

    return current_display_language()


def current_display_language():
    """
    Get the current display language ("zh_CN" when the translations are
    displayed, "en" when the original texts are displayed).
    """

    return language if (active and language) else 'en'





def translate_widgets(builder):
    """
    Translate the translatable texts of all widgets that were loaded by
    the builder (labels, buttons, menu items, window titles, etc.). This
    function should be invoked after all user interface files were
    loaded into the builder.

    Arguments:
    builder : Gtk.Builder
        The builder that contains all of the widgets.
    """

    if not translations and not inverse_translations: return

    import gi
    from gi.repository import Gtk

    for obj in builder.get_objects():
        if not isinstance(obj, Gtk.Widget): continue
        # Do not translate editable widgets (the text is user content).
        if isinstance(obj, Gtk.Editable): continue
        for property_name in ('label', 'title', 'text'):
            try:
                # Only widgets that support the property.
                if not obj.find_property(property_name): continue
                value = obj.get_property(property_name)
                if not isinstance(value, str) or not value: continue
                translated_value = tr(value)
                if translated_value and translated_value != value:
                    obj.set_property(property_name, translated_value)
            except (AttributeError, TypeError, ValueError):
                continue
