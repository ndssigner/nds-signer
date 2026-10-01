/*
 * NDS-Signer - `nds` MicroPython module: the DSi hardware seen from Python.
 * SPDX-License-Identifier: MIT
 *
 * Deliberately small: primitives only. Layout, buttons and screen logic live
 * in Python (NDS-Signer's seedsigner.gui) so they can be tested on the host
 * against tests/host/sim/nds.py, which implements this same API.
 * Hardware access goes through arm9/include/nds_bridge.h (no libnds here).
 */
#include "py/mperrno.h"
#include "py/obj.h"
#include "py/runtime.h"

#include <string.h>

#include "nds_bridge.h"
#include "gfx_fonts.h"  /* build/generated: GFX_FONT_* ids */
#include "sfx.h"        /* SFX_* ids (plain C) */

static mp_obj_t print_on(int screen, mp_obj_t row, mp_obj_t col, mp_obj_t text_in)
{
	size_t len;
	const char *text = mp_obj_str_get_data(text_in, &len);
	ndsbPrint(screen, mp_obj_get_int(row), mp_obj_get_int(col), text, len);
	return mp_const_none;
}

/* top_print(row, col, text) / bottom_print(...): col < 0 centres the text */
static mp_obj_t nds_top_print(mp_obj_t row, mp_obj_t col, mp_obj_t text)
{
	return print_on(NDSB_TOP, row, col, text);
}
static MP_DEFINE_CONST_FUN_OBJ_3(nds_top_print_obj, nds_top_print);

static mp_obj_t nds_bottom_print(mp_obj_t row, mp_obj_t col, mp_obj_t text)
{
	return print_on(NDSB_BOTTOM, row, col, text);
}
static MP_DEFINE_CONST_FUN_OBJ_3(nds_bottom_print_obj, nds_bottom_print);

static mp_obj_t nds_top_clear(void)
{
	ndsbClear(NDSB_TOP);
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_top_clear_obj, nds_top_clear);

static mp_obj_t nds_bottom_clear(void)
{
	ndsbClear(NDSB_BOTTOM);
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_bottom_clear_obj, nds_bottom_clear);

/* frame(): wait for the next VBlank and sample the keys (once per frame) */
static mp_obj_t nds_frame(void)
{
	ndsbFrame();
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_frame_obj, nds_frame);

static mp_obj_t nds_keys_down(void)
{
	return mp_obj_new_int(ndsbKeysDown());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_keys_down_obj, nds_keys_down);

static mp_obj_t nds_keys_held(void)
{
	return mp_obj_new_int(ndsbKeysHeld());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_keys_held_obj, nds_keys_held);

/* touch(): (x, y) in bottom-screen pixels while the stylus is down, else None */
static mp_obj_t nds_touch(void)
{
	int x, y;
	if (!ndsbTouch(&x, &y))
		return mp_const_none;
	mp_obj_t xy[2] = { mp_obj_new_int(x), mp_obj_new_int(y) };
	return mp_obj_new_tuple(2, xy);
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_touch_obj, nds_touch);

static mp_obj_t nds_ticks_ms(void)
{
	return mp_obj_new_int_from_uint(ndsbTicksMs());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_ticks_ms_obj, nds_ticks_ms);

/* camera_init(): powers up the DSi cameras; False in DS mode / no camera */
static mp_obj_t nds_camera_init(void)
{
	return mp_obj_new_bool(ndsbCameraInit());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_init_obj, nds_camera_init);

static mp_obj_t nds_camera_start(size_t n_args, const mp_obj_t *args)
{
	/* camera_start(front=False): the outer camera, or the inner one */
	return mp_obj_new_bool(ndsbCameraStart(n_args > 0 && mp_obj_is_true(args[0])));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_camera_start_obj, 0, 1, nds_camera_start);

/* camera_grab(buf): the raw frame (YUV422 640x480, CAMERA_FRAME_BYTES) of
 * the last camera_poll() into `buf`, each frame once: 0 = no new frame,
 * 1 = copied, 2 = copied but flat (every pixel identical) */
static mp_obj_t nds_camera_grab(mp_obj_t buf_in)
{
	mp_buffer_info_t buf;
	mp_get_buffer_raise(buf_in, &buf, MP_BUFFER_WRITE);
	return mp_obj_new_int(ndsbCameraGrab(buf.buf, buf.len));
}
static MP_DEFINE_CONST_FUN_OBJ_1(nds_camera_grab_obj, nds_camera_grab);

/* camera_running(): True between camera_start() and camera_stop() */
static mp_obj_t nds_camera_running(void)
{
	return mp_obj_new_bool(ndsbCameraRunning());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_running_obj, nds_camera_running);

/* frame_show(screen, frame): a raw camera frame in grey, shown at once */
static mp_obj_t nds_frame_show(mp_obj_t screen, mp_obj_t frame_in)
{
	mp_buffer_info_t buf;
	mp_get_buffer_raise(frame_in, &buf, MP_BUFFER_READ);
	ndsbFrameShow(mp_obj_get_int(screen), buf.buf, buf.len);
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(nds_frame_show_obj, nds_frame_show);

/* camera_decode(on): decoding on, or preview only */
static mp_obj_t nds_camera_decode(mp_obj_t on)
{
	ndsbCameraDecode(mp_obj_is_true(on));
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(nds_camera_decode_obj, nds_camera_decode);

/* camera_poll(): processes at most one frame (live preview on the top
 * screen). Returns the decoded QR payload as bytes, or None. */
static mp_obj_t nds_camera_poll(void)
{
	static uint8_t buf[NDSB_MAX_PAYLOAD];
	size_t len = 0;
	int r = ndsbCameraPoll(buf, &len);
	if (r < 0)
		mp_raise_OSError(MP_EIO);
	if (r == 0)
		return mp_const_none;
	mp_obj_t result = mp_obj_new_bytes(buf, len);
	/* the payload may be secret (SeedQR): wipe the static copy */
	for (size_t i = 0; i < len; i++)
		((volatile uint8_t *)buf)[i] = 0;
	return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_poll_obj, nds_camera_poll);

static mp_obj_t nds_camera_stop(void)
{
	ndsbCameraStop();
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_stop_obj, nds_camera_stop);

/* camera_stats(): (frames processed, last decode ms, frames with a QR
 * candidate, frames decoded, total us in luma copy / quirc identify / quirc
 * decode, ms since camera_start(), grids refined, transfer restarts) */
static mp_obj_t nds_camera_stats(void)
{
	uint32_t stats[NDSB_CAMERA_STATS];
	mp_obj_t t[NDSB_CAMERA_STATS];
	ndsbCameraStats(stats);
	for (int i = 0; i < NDSB_CAMERA_STATS; i++)
		t[i] = mp_obj_new_int_from_uint(stats[i]);
	return mp_obj_new_tuple(NDSB_CAMERA_STATS, t);
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_stats_obj, nds_camera_stats);

/* scan_benchmark(text, pixels): decodes `text` drawn as a QR code about
 * `pixels` wide in a synthetic 640x480 frame, without the camera.
 * Returns (decoded_ok, copy_us, identify_us, decode_us, otsu_us, binarize_us,
 * finder_us, grouping_us, jiggle_us) or None; the stage times are 0 in release builds. */
static mp_obj_t nds_scan_benchmark(mp_obj_t text_in, mp_obj_t pixels_in)
{
	size_t len;
	const char *text = mp_obj_str_get_data(text_in, &len);
	uint32_t times[8];
	int r = ndsbScanBenchmark(text, len, mp_obj_get_int(pixels_in), times);
	if (r < 0)
		return mp_const_none;
	mp_obj_t t[9] = { mp_obj_new_bool(r) };
	for (int i = 0; i < 8; i++)
		t[1 + i] = mp_obj_new_int_from_uint(times[i]);
	return mp_obj_new_tuple(9, t);
}
static MP_DEFINE_CONST_FUN_OBJ_2(nds_scan_benchmark_obj, nds_scan_benchmark);

/* qr_show(text, border=2, background=255): QR code on the top screen.
 * Returns its size in modules (0 if the text does not fit). */
static mp_obj_t nds_qr_show(size_t n_args, const mp_obj_t *args)
{
	size_t len;
	const char *text = mp_obj_str_get_data(args[0], &len);
	int border = n_args > 1 ? mp_obj_get_int(args[1]) : 2;
	int background = n_args > 2 ? mp_obj_get_int(args[2]) : 255;
	return mp_obj_new_int(ndsbQrShow(text, len, border, background));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_qr_show_obj, 1, 3, nds_qr_show);

/* ---- graphical UI (arm9/include/gfx.h): screen 0 top / 1 bottom, colors
 * 0xRRGGBB, fonts FONT_*; draw, then gfx_present(screen) ---- */
static mp_obj_t nds_gfx_clear(mp_obj_t screen, mp_obj_t rgb)
{
	ndsbGfxClear(mp_obj_get_int(screen), mp_obj_get_int(rgb));
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(nds_gfx_clear_obj, nds_gfx_clear);

/* gfx_rect(screen, x, y, w, h, rgb, radius=0) */
static mp_obj_t nds_gfx_rect(size_t n_args, const mp_obj_t *a)
{
	ndsbGfxRect(mp_obj_get_int(a[0]), mp_obj_get_int(a[1]), mp_obj_get_int(a[2]),
	            mp_obj_get_int(a[3]), mp_obj_get_int(a[4]), mp_obj_get_int(a[5]),
	            n_args > 6 ? mp_obj_get_int(a[6]) : 0);
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_gfx_rect_obj, 6, 7, nds_gfx_rect);

/* gfx_frame(screen, x, y, w, h, rgb, radius=0, thickness=1) */
static mp_obj_t nds_gfx_frame(size_t n_args, const mp_obj_t *a)
{
	ndsbGfxFrame(mp_obj_get_int(a[0]), mp_obj_get_int(a[1]), mp_obj_get_int(a[2]),
	             mp_obj_get_int(a[3]), mp_obj_get_int(a[4]), mp_obj_get_int(a[5]),
	             n_args > 6 ? mp_obj_get_int(a[6]) : 0, n_args > 7 ? mp_obj_get_int(a[7]) : 1);
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_gfx_frame_obj, 6, 8, nds_gfx_frame);

/* gfx_text(screen, x, y, text, font, rgb, max_width=0) -> width drawn;
 * (x, y) is the top-left corner of the line box */
static mp_obj_t nds_gfx_text(size_t n_args, const mp_obj_t *a)
{
	size_t len;
	const char *text = mp_obj_str_get_data(a[3], &len);
	return mp_obj_new_int(ndsbGfxText(mp_obj_get_int(a[0]), mp_obj_get_int(a[1]),
	                                  mp_obj_get_int(a[2]), text, len, mp_obj_get_int(a[4]),
	                                  mp_obj_get_int(a[5]), n_args > 6 ? mp_obj_get_int(a[6]) : 0));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_gfx_text_obj, 6, 7, nds_gfx_text);

static mp_obj_t nds_gfx_text_width(mp_obj_t text_in, mp_obj_t font)
{
	size_t len;
	const char *text = mp_obj_str_get_data(text_in, &len);
	return mp_obj_new_int(ndsbGfxTextWidth(text, len, mp_obj_get_int(font)));
}
static MP_DEFINE_CONST_FUN_OBJ_2(nds_gfx_text_width_obj, nds_gfx_text_width);

/* gfx_font_metrics(font) -> (ascent, line_height) */
static mp_obj_t nds_gfx_font_metrics(mp_obj_t font)
{
	int ascent, line;
	ndsbGfxFontMetrics(mp_obj_get_int(font), &ascent, &line);
	mp_obj_t t[2] = { mp_obj_new_int(ascent), mp_obj_new_int(line) };
	return mp_obj_new_tuple(2, t);
}
static MP_DEFINE_CONST_FUN_OBJ_1(nds_gfx_font_metrics_obj, nds_gfx_font_metrics);

/* system_language(): the console's language setting (0 Japanese, 1 English,
 * 2 French, 3 German, 4 Italian, 5 Spanish, 6 Chinese, 7 Korean) */
static mp_obj_t nds_system_language(void)
{
	return mp_obj_new_int(ndsbSystemLanguage());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_system_language_obj, nds_system_language);

/* sound(effect): a UI feedback sound, SFX_* */
static mp_obj_t nds_sound(mp_obj_t effect)
{
	ndsbSound(mp_obj_get_int(effect));
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(nds_sound_obj, nds_sound);

static mp_obj_t nds_gfx_present(mp_obj_t screen)
{
	ndsbGfxPresent(mp_obj_get_int(screen));
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(nds_gfx_present_obj, nds_gfx_present);

/* qr_transcribe(data, zone_modules=0, zone_x=0, zone_y=0): SeedQR for hand
 * transcription on the top screen, ECC L exactly; bytes data is encoded in
 * binary mode (CompactSeedQR). zone_modules > 0 zooms into one zone.
 * Returns the QR size in modules (0 if the data does not fit). */
static mp_obj_t nds_qr_transcribe(size_t n_args, const mp_obj_t *args)
{
	size_t len;
	const char *data;
	bool binary = !mp_obj_is_str(args[0]);
	if (binary) {
		mp_buffer_info_t buf;
		mp_get_buffer_raise(args[0], &buf, MP_BUFFER_READ);
		data = buf.buf;
		len = buf.len;
	} else {
		data = mp_obj_str_get_data(args[0], &len);
	}
	int zoneModules = n_args > 1 ? mp_obj_get_int(args[1]) : 0;
	int zoneX = n_args > 2 ? mp_obj_get_int(args[2]) : 0;
	int zoneY = n_args > 3 ? mp_obj_get_int(args[3]) : 0;
	return mp_obj_new_int(ndsbQrTranscribe((const uint8_t *)data, len, binary,
	                                       zoneModules, zoneX, zoneY));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_qr_transcribe_obj, 1, 4, nds_qr_transcribe);

/* qr_draw(screen, text, x, y, px): a QR code in a px x px box of the back
 * buffer (gfx_present() shows it); returns its size in modules, 0 if the
 * text does not fit */
static mp_obj_t nds_qr_draw(size_t n_args, const mp_obj_t *args)
{
	(void)n_args;
	size_t len;
	const char *text = mp_obj_str_get_data(args[1], &len);
	return mp_obj_new_int(ndsbQrDraw(mp_obj_get_int(args[0]), text, len, mp_obj_get_int(args[2]),
	                                 mp_obj_get_int(args[3]), mp_obj_get_int(args[4])));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_qr_draw_obj, 5, 5, nds_qr_draw);

/* qr_transcribe_map(screen, x, y, scale, zone_modules, zone_x, zone_y): a map
 * of the code last shown by qr_transcribe(), the zone highlighted (back
 * buffer; gfx_present() shows it) */
static mp_obj_t nds_qr_transcribe_map(size_t n_args, const mp_obj_t *args)
{
	(void)n_args;
	ndsbQrTranscribeMap(mp_obj_get_int(args[0]), mp_obj_get_int(args[1]), mp_obj_get_int(args[2]),
	                    mp_obj_get_int(args[3]), mp_obj_get_int(args[4]), mp_obj_get_int(args[5]),
	                    mp_obj_get_int(args[6]));
	return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(nds_qr_transcribe_map_obj, 7, 7, nds_qr_transcribe_map);

/* info(): (dsi_mode, camera_ok, c_heap_kb, uptime_s) */
static mp_obj_t nds_info(void)
{
	NdsbInfo info;
	ndsbInfo(&info);
	mp_obj_t t[4] = {
		mp_obj_new_bool(info.dsiMode), mp_obj_new_bool(info.cameraOk),
		mp_obj_new_int(info.cHeapKB), mp_obj_new_int(info.uptimeS),
	};
	return mp_obj_new_tuple(4, t);
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_info_obj, nds_info);

static mp_obj_t nds_version(void)
{
	return mp_obj_new_str(ndsbVersion(), strlen(ndsbVersion()));
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_version_obj, nds_version);

static const mp_rom_map_elem_t nds_module_globals_table[] = {
	{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_nds) },
	{ MP_ROM_QSTR(MP_QSTR_COLS), MP_ROM_INT(NDSB_COLS) },
	{ MP_ROM_QSTR(MP_QSTR_ROWS), MP_ROM_INT(NDSB_ROWS) },
	{ MP_ROM_QSTR(MP_QSTR_top_print), MP_ROM_PTR(&nds_top_print_obj) },
	{ MP_ROM_QSTR(MP_QSTR_bottom_print), MP_ROM_PTR(&nds_bottom_print_obj) },
	{ MP_ROM_QSTR(MP_QSTR_top_clear), MP_ROM_PTR(&nds_top_clear_obj) },
	{ MP_ROM_QSTR(MP_QSTR_bottom_clear), MP_ROM_PTR(&nds_bottom_clear_obj) },
	{ MP_ROM_QSTR(MP_QSTR_frame), MP_ROM_PTR(&nds_frame_obj) },
	{ MP_ROM_QSTR(MP_QSTR_keys_down), MP_ROM_PTR(&nds_keys_down_obj) },
	{ MP_ROM_QSTR(MP_QSTR_keys_held), MP_ROM_PTR(&nds_keys_held_obj) },
	{ MP_ROM_QSTR(MP_QSTR_touch), MP_ROM_PTR(&nds_touch_obj) },
	{ MP_ROM_QSTR(MP_QSTR_ticks_ms), MP_ROM_PTR(&nds_ticks_ms_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_init), MP_ROM_PTR(&nds_camera_init_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_start), MP_ROM_PTR(&nds_camera_start_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_poll), MP_ROM_PTR(&nds_camera_poll_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_stop), MP_ROM_PTR(&nds_camera_stop_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_stats), MP_ROM_PTR(&nds_camera_stats_obj) },
	{ MP_ROM_QSTR(MP_QSTR_scan_benchmark), MP_ROM_PTR(&nds_scan_benchmark_obj) },
	{ MP_ROM_QSTR(MP_QSTR_qr_show), MP_ROM_PTR(&nds_qr_show_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_clear), MP_ROM_PTR(&nds_gfx_clear_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_rect), MP_ROM_PTR(&nds_gfx_rect_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_frame), MP_ROM_PTR(&nds_gfx_frame_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_text), MP_ROM_PTR(&nds_gfx_text_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_text_width), MP_ROM_PTR(&nds_gfx_text_width_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_font_metrics), MP_ROM_PTR(&nds_gfx_font_metrics_obj) },
	{ MP_ROM_QSTR(MP_QSTR_gfx_present), MP_ROM_PTR(&nds_gfx_present_obj) },
	{ MP_ROM_QSTR(MP_QSTR_sound), MP_ROM_PTR(&nds_sound_obj) },
	{ MP_ROM_QSTR(MP_QSTR_system_language), MP_ROM_PTR(&nds_system_language_obj) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_CLICK), MP_ROM_INT(SFX_CLICK) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_KEY), MP_ROM_INT(SFX_KEY) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_BACK), MP_ROM_INT(SFX_BACK) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_SUCCESS), MP_ROM_INT(SFX_SUCCESS) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_WARNING), MP_ROM_INT(SFX_WARNING) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_ERROR), MP_ROM_INT(SFX_ERROR) },
	{ MP_ROM_QSTR(MP_QSTR_SFX_SCAN), MP_ROM_INT(SFX_SCAN) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_BODY), MP_ROM_INT(GFX_FONT_BODY) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_BODY_BOLD), MP_ROM_INT(GFX_FONT_BODY_BOLD) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_BUTTON), MP_ROM_INT(GFX_FONT_BUTTON) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_TITLE), MP_ROM_INT(GFX_FONT_TITLE) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_LARGE), MP_ROM_INT(GFX_FONT_LARGE) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_MONO), MP_ROM_INT(GFX_FONT_MONO) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_MONO_SMALL), MP_ROM_INT(GFX_FONT_MONO_SMALL) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_MONO_BOLD), MP_ROM_INT(GFX_FONT_MONO_BOLD) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_ICON), MP_ROM_INT(GFX_FONT_ICON) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_ICON_LARGE), MP_ROM_INT(GFX_FONT_ICON_LARGE) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_SSICON), MP_ROM_INT(GFX_FONT_SSICON) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_SSICON_LARGE), MP_ROM_INT(GFX_FONT_SSICON_LARGE) },
	{ MP_ROM_QSTR(MP_QSTR_FONT_SSICON_HUGE), MP_ROM_INT(GFX_FONT_SSICON_HUGE) },
	{ MP_ROM_QSTR(MP_QSTR_qr_transcribe), MP_ROM_PTR(&nds_qr_transcribe_obj) },
	{ MP_ROM_QSTR(MP_QSTR_qr_transcribe_map), MP_ROM_PTR(&nds_qr_transcribe_map_obj) },
	{ MP_ROM_QSTR(MP_QSTR_qr_draw), MP_ROM_PTR(&nds_qr_draw_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_decode), MP_ROM_PTR(&nds_camera_decode_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_grab), MP_ROM_PTR(&nds_camera_grab_obj) },
	{ MP_ROM_QSTR(MP_QSTR_camera_running), MP_ROM_PTR(&nds_camera_running_obj) },
	{ MP_ROM_QSTR(MP_QSTR_frame_show), MP_ROM_PTR(&nds_frame_show_obj) },
	{ MP_ROM_QSTR(MP_QSTR_CAMERA_FRAME_BYTES), MP_ROM_INT(640 * 480 * 2) },
	{ MP_ROM_QSTR(MP_QSTR_info), MP_ROM_PTR(&nds_info_obj) },
	{ MP_ROM_QSTR(MP_QSTR_version), MP_ROM_PTR(&nds_version_obj) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_A), MP_ROM_INT(NDSB_KEY_A) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_B), MP_ROM_INT(NDSB_KEY_B) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_X), MP_ROM_INT(NDSB_KEY_X) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_Y), MP_ROM_INT(NDSB_KEY_Y) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_START), MP_ROM_INT(NDSB_KEY_START) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_SELECT), MP_ROM_INT(NDSB_KEY_SELECT) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_UP), MP_ROM_INT(NDSB_KEY_UP) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_DOWN), MP_ROM_INT(NDSB_KEY_DOWN) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_LEFT), MP_ROM_INT(NDSB_KEY_LEFT) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_RIGHT), MP_ROM_INT(NDSB_KEY_RIGHT) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_L), MP_ROM_INT(NDSB_KEY_L) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_R), MP_ROM_INT(NDSB_KEY_R) },
	{ MP_ROM_QSTR(MP_QSTR_KEY_TOUCH), MP_ROM_INT(NDSB_KEY_TOUCH) },
};
static MP_DEFINE_CONST_DICT(nds_module_globals, nds_module_globals_table);

const mp_obj_module_t nds_user_cmodule = {
	.base = { &mp_type_module },
	.globals = (mp_obj_dict_t *)&nds_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_nds, nds_user_cmodule);
