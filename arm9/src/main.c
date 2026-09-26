/*
 * NDS-Signer - Air-gapped Bitcoin PSBT signer for Nintendo DSi / 3DS
 * SPDX-License-Identifier: MIT
 *
 * Phase 3: SeedSigner-style main menu and QR scanning.
 * Screen flow and texts are ported from SeedSigner's MainMenuView and ScanView
 * (src/seedsigner/views/view.py, scan_views.py; MIT).
 */
#include <nds.h>
#include <stdio.h>
#include <string.h>

#include "qr_scanner.h"
#include "quirc.h"
#include "qr_type.h"
#include "ui.h"

#define APP_VERSION "0.3.0-dev"

#ifdef NDS_SIGNER_MPY_SPIKE
void mpySpikeRun(void);
#endif

typedef enum { SCREEN_HOME, SCREEN_SCAN, SCREEN_RESULT, SCREEN_EXIT } Screen;

static bool s_haveCamera;

/* ------------------------------------------------------------------ home */

enum { HOME_SCAN, HOME_SEEDS, HOME_TOOLS, HOME_SETTINGS, HOME_EXIT, HOME_COUNT };

static const UiButton s_homeButtons[HOME_COUNT] = {
	[HOME_SCAN]     = { 1, 3, 14, "Scan" },
	[HOME_SEEDS]    = { 17, 3, 14, "Seeds" },
	[HOME_TOOLS]    = { 1, 8, 14, "Tools" },
	[HOME_SETTINGS] = { 17, 8, 14, "Settings" },
	[HOME_EXIT]     = { 9, 19, 14, "Exit" },
};

static Screen homeScreen(void)
{
	/* MainMenuView: title "Home" */
	uiClearTop();
	uiPrintCentered(1, "Home");
	uiPrintCentered(8, "NDS-Signer");
	uiPrintCentered(10, "Air-gapped Bitcoin signer");
	uiPrintCentered(12, "v" APP_VERSION);
	uiPrintCentered(22, isDSiMode() ? "DSi mode" : "DS mode");
	if (!s_haveCamera)
		uiPrintCentered(16, "No camera available");

	uiClearBottom();
	uiDrawButtons(s_homeButtons, HOME_COUNT);

	for (;;) {
		swiWaitForVBlank();
		scanKeys();
		if (keysDown() & KEY_START)
			return SCREEN_EXIT;

		switch (uiPollButtons(s_homeButtons, HOME_COUNT)) {
		case HOME_SCAN:
			if (s_haveCamera)
				return SCREEN_SCAN;
			consoleSelect(&g_uiBottom);
			uiPrintCentered(15, "No camera available ");
			break;
		case HOME_SEEDS:
		case HOME_TOOLS:
		case HOME_SETTINGS:
			consoleSelect(&g_uiBottom);
			uiPrintCentered(15, "Not implemented yet ");
			break;
		case HOME_EXIT:
			return SCREEN_EXIT;
		}
	}
}

/* ------------------------------------------------------------------ scan */

enum { SCAN_CANCEL, SCAN_BUTTON_COUNT };

static const UiButton s_scanButtons[SCAN_BUTTON_COUNT] = {
	[SCAN_CANCEL] = { 9, 19, 14, "Cancel" },
};

static Screen scanScreen(void)
{
	/* ScanView.instructions_text, drawn over the live preview */
	uiClearTop();
	uiPrintCentered(22, "Scan a QR code");
	uiClearBottom();
	uiDrawButtons(s_scanButtons, SCAN_BUTTON_COUNT);

	if (!scannerStart()) {
		printf("\x1b[3;0HCamera error");
		return SCREEN_HOME;
	}

	Screen next = SCREEN_HOME;
	for (;;) {
		swiWaitForVBlank();
		scanKeys();
		if ((keysDown() & KEY_B) || uiPollButtons(s_scanButtons, SCAN_BUTTON_COUNT) == SCAN_CANCEL)
			break;

		ScanStatus st = scannerPoll(uiTopBitmap());
		if (st == SCAN_IDLE)
			continue;
		if (st == SCAN_ERROR)
			break;

		const ScanStats *stats = scannerStats();
		consoleSelect(&g_uiBottom);
		printf("\x1b[3;0HFrames:  %-8lu", (unsigned long)stats->frames);
		printf("\x1b[4;0HDecode:  %4lu ms   ", (unsigned long)(stats->lastDecodeUs / 1000));
		printf("\x1b[5;0HQR seen: %-3d", stats->lastGrids);
		printf("\x1b[6;0HError:   %-20s", stats->lastError ? quirc_strerror(stats->lastError) : "-");

		if (st == SCAN_DECODED) {
			next = SCREEN_RESULT;
			break;
		}
	}

	scannerStop();
	return next;
}

/* ---------------------------------------------------------------- result */

/* SeedSigner shows QR types as e.g. "seed: compactseedqr":
 *   qr_type.replace("__", ": ").replace("_", " ") */
static void formatQrType(QrType type, char *out, size_t size)
{
	const char *name = qrTypeName(type);
	size_t o = 0;
	for (size_t i = 0; name[i] && o + 3 < size; i++) {
		if (name[i] == '_' && name[i + 1] == '_') {
			out[o++] = ':';
			out[o++] = ' ';
			i++;
		} else {
			out[o++] = name[i] == '_' ? ' ' : name[i];
		}
	}
	out[o] = '\0';
}

/* Port of the routing at the end of SeedSigner's ScanView.run(). Until the
 * seed / PSBT / address flows are ported, recognised types end up in
 * NotYetImplementedView, as SeedSigner itself does for unsupported ones. */
static Screen resultScreen(void)
{
	size_t len;
	const u8 *payload = scannerPayload(&len);
	QrType type = qrDetectSegmentType(payload, len);

	/* The payload is no longer needed: never leave it (possibly a seed) in RAM */
	scannerClearPayload();

	if (type == QR_INVALID) {
		/* ScanInvalidQRTypeView */
		uiWarningScreen("Error", "Unknown QR Type",
		                "QRCode is invalid or is a data format not yet supported.",
		                NULL, "Back to Main Menu");
		return SCREEN_HOME;
	}

	/* NotYetImplementedView, plus the detected type for development */
	char typeText[40], detail[64];
	formatQrType(type, typeText, sizeof(typeText));
	snprintf(detail, sizeof(detail), "Detected: %s (%u bytes)", typeText, (unsigned)len);
	uiWarningScreen("Work In Progress", "Not Yet Implemented",
	                "This is still on our to-do list!", detail, "Back to main menu");
	return SCREEN_HOME;
}

/* ------------------------------------------------------------------ main */

/* The default ARM9 stack lives in the 16 KB DTCM, too small for quirc
 * (quirc_decode alone keeps ~13 KB on the stack). The app runs in a thread
 * with a larger stack in main RAM instead. */
#define APP_STACK_SIZE (128 * 1024)

static Thread s_appThread;
alignas(8) static u8 s_appStack[APP_STACK_SIZE];

static int appMain(void *arg)
{
	(void)arg;

	/* 134 MHz ARM9 on DSi: QR decoding is CPU bound */
	if (isDSiMode())
		setCpuClock(true);

	uiInit();
#ifdef NDS_SIGNER_MPY_SPIKE
	mpySpikeRun();
	for (;;)
		swiWaitForVBlank();
#endif
	s_haveCamera = scannerInit();

	Screen screen = SCREEN_HOME;
#ifdef NDS_SIGNER_AUTOTEST
	if (s_haveCamera)
		screen = SCREEN_SCAN;
#endif
	while (screen != SCREEN_EXIT) {
		switch (screen) {
		case SCREEN_HOME:   screen = homeScreen(); break;
		case SCREEN_SCAN:   screen = scanScreen(); break;
		case SCREEN_RESULT: screen = resultScreen(); break;
		default:            screen = SCREEN_EXIT; break;
		}
	}

	/* Turns the camera (and its LED) off and wipes buffers */
	scannerShutdown();
	return 0;
}

int main(void)
{
	threadPrepare(&s_appThread, appMain, NULL, &s_appStack[APP_STACK_SIZE], MAIN_THREAD_PRIO);
	threadStart(&s_appThread);
	return threadJoin(&s_appThread);
}
