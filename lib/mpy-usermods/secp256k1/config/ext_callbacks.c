/*
 * NDS-Signer: libsecp256k1 callbacks (USE_EXTERNAL_DEFAULT_CALLBACKS).
 * SPDX-License-Identifier: MIT
 *
 * The secp256k1-embedded originals were empty functions, so an internal
 * library error would have been ignored. libsecp256k1's defaults abort();
 * here the error callback halts the console instead (never returns).
 * The illegal-argument callback may return: the API call then fails
 * (returns 0), which the wrapper turns into a Python exception.
 */
void secp256k1_default_illegal_callback_fn(const char *str, void *data)
{
	(void)str;
	(void)data;
}

void secp256k1_default_error_callback_fn(const char *str, void *data)
{
	(void)str;
	(void)data;
	for (;;) {
		/* internal error in libsecp256k1: stop, never continue signing */
	}
}
