"""PAS manager module."""
import os
import time
import traceback
from datetime import datetime

import pyautogui
from pynput.keyboard import Key, Controller
from graphic_detecter import GraphicDetecter
from utils import log

_DEFAULT_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 2


class PASManager:
    """Manager for PAS (Presentation Audio Sharing) related logic."""

    def __init__(self, max_retries: int = _DEFAULT_MAX_RETRIES):
        self._keyboard = Controller()
        self._detecter = GraphicDetecter(default_confidence=0.7)
        self._error_screenshot_folder = os.path.join("report", "pas_errors")
        self._max_retries = max_retries
        self._headset_1: str = ""
        self._headset_2: str = ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _open_pas_board(self) -> None:
        """Open the PAS sharing board via Win+A then Enter."""
        with self._keyboard.pressed(Key.cmd):
            self._keyboard.press('a')
            self._keyboard.release('a')
        time.sleep(3)
        self._keyboard.press(Key.enter)
        self._keyboard.release(Key.enter)
        log.info("Pressed Win+A then Enter to open PAS sharing board.")

    def _close_pas_board(self) -> None:
        """Close the PAS sharing board via Win+A."""
        with self._keyboard.pressed(Key.cmd):
            self._keyboard.press('a')
            self._keyboard.release('a')
        log.info("Pressed Win+A to close PAS sharing board.")

    def _save_error_screenshot(self, label: str = "error") -> None:
        """Capture and save a labelled screenshot for PAS failures."""
        os.makedirs(self._error_screenshot_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            self._error_screenshot_folder,
            f"pas_{label}_{timestamp}.png",
        )
        pyautogui.screenshot(screenshot_path)
        log.info("Saved PAS error screenshot: %s", screenshot_path)

    def prepare(self, headset_1: str, headset_2: str) -> None:
        """
        Prepare the PAS manager with two headset identifiers.

        Args:
            headset_1: Identifier or name of the first headset.
            headset_2: Identifier or name of the second headset.
        """
        self._headset_1 = headset_1
        self._headset_2 = headset_2
        log.info(
            "PASManager prepared with headset_1=%s, headset_2=%s",
            headset_1,
            headset_2,
        )


    def start_sharing(self, path: str) -> bool:
        """
        Start sharing by clicking the UI element matched by the given image.

        Retries up to max_retries times on failure.

        Args:
            path: Folder containing pas_select.png and pas_share.png.

        Returns:
            True if sharing started successfully, False otherwise.
        """
        for attempt in range(1, self._max_retries + 1):
            log.info("start_sharing attempt %d/%d", attempt, self._max_retries)
            self._open_pas_board()
            time.sleep(3)
            try:
                # Step 1: click pas_select.png
                pas_select = os.path.join(path, "pas_select.png")
                if not self._detecter.find_and_click(pas_select):
                    log.warning("pas_select.png not found: %s", pas_select)
                    self._save_error_screenshot("start_select_missing")
                    continue
                log.info("Clicked pas_select.png, waiting 3 seconds...")
                time.sleep(3)

                # Step 2: click pas_share.png
                pas_share = os.path.join(path, "pas_share.png")
                if not self._detecter.find_and_click(pas_share):
                    log.warning("pas_share.png not found: %s", pas_share)
                    self._save_error_screenshot("start_share_missing")
                    continue
                log.info("Clicked pas_share.png, sharing started.")
                return True
            except Exception as exc:
                log.error(
                    "start_sharing attempt %d raised unexpected error: %s\n%s",
                    attempt, exc, traceback.format_exc(),
                )
                self._save_error_screenshot(f"start_unexpected_attempt{attempt}")
            finally:
                self._close_pas_board()

            if attempt < self._max_retries:
                log.info("Retrying start_sharing in %s seconds...", _RETRY_DELAY_SEC)
                time.sleep(_RETRY_DELAY_SEC)

        log.error("start_sharing failed after %d attempts.", self._max_retries)
        return False

    def stop_sharing(self, path: str) -> bool:
        """
        Stop sharing by clicking the UI element matched by the given image.

        Retries up to max_retries times on failure.

        Args:
            path: Folder containing pas_stop_share.png.

        Returns:
            True if sharing stopped successfully, False otherwise.
        """
        for attempt in range(1, self._max_retries + 1):
            log.info("stop_sharing attempt %d/%d", attempt, self._max_retries)
            self._open_pas_board()
            time.sleep(3)
            try:
                pas_stop_share = os.path.join(path, "pas_stop_share.png")
                if not self._detecter.find_and_click(pas_stop_share):
                    log.warning("pas_stop_share.png not found: %s", pas_stop_share)
                    self._save_error_screenshot("stop_share_missing")
                    continue
                log.info("Clicked pas_stop_share.png, sharing stopped.")
                return True
            except Exception as exc:
                log.error(
                    "stop_sharing attempt %d raised unexpected error: %s\n%s",
                    attempt, exc, traceback.format_exc(),
                )
                self._save_error_screenshot(f"stop_unexpected_attempt{attempt}")
            finally:
                time.sleep(3)
                self._close_pas_board()

            if attempt < self._max_retries:
                log.info("Retrying stop_sharing in %s seconds...", _RETRY_DELAY_SEC)
                time.sleep(_RETRY_DELAY_SEC)

        log.error("stop_sharing failed after %d attempts.", self._max_retries)
        return False


if __name__ == "__main__":
    manager = PASManager()
    result = manager.start_sharing("pas")
    print(f"start_sharing result: {result}")
    time.sleep(10)
    result = manager.stop_sharing("pas")
    print(f"stop_sharing result: {result}")

