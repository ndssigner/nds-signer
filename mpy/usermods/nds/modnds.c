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

#include "nds_bridge.h"

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

static mp_obj_t nds_camera_start(void)
{
	return mp_obj_new_bool(ndsbCameraStart());
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_start_obj, nds_camera_start);

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

/* camera_stats(): (frames processed, last decode time in ms) */
static mp_obj_t nds_camera_stats(void)
{
	uint32_t frames, ms;
	ndsbCameraStats(&frames, &ms);
	mp_obj_t t[2] = { mp_obj_new_int(frames), mp_obj_new_int(ms) };
	return mp_obj_new_tuple(2, t);
}
static MP_DEFINE_CONST_FUN_OBJ_0(nds_camera_stats_obj, nds_camera_stats);

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
	{ MP_ROM_QSTR(MP_QSTR_qr_show), MP_ROM_PTR(&nds_qr_show_obj) },
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
