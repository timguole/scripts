// A simple PAM auth program for OpenVPN
//
// How to compile:
// $ sudo apt install libpam0g-dev
// $ gcc pamauth.c -lpam -o pamauth
// $ sudo chown root:root pamauth
// $ sudo chmod 4755 pamauth
//
// How to use:
// In openvpn server config file:
// 		auth-user-pass-verify pamauth

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <security/pam_appl.h>


// return code
#define PAMAUTH_OK 0
#define PAMAUTH_ERROR 1

// username and password length limit
#define MAX_LEN 31

static const char *username = NULL;
static const char *password = NULL;

static int auth_conv(int num_msg, const struct pam_message **msg,
		struct pam_response **resp, void *appdata_ptr)
{
	if ((num_msg <= 0) || (num_msg > PAM_MAX_NUM_MSG)) {
		goto bailout;
	}

	struct pam_response *resp_array = calloc(num_msg,  sizeof(struct pam_response));
	if (resp_array == NULL) {
		goto bailout;
	}

	const struct pam_message *msg_array = *msg;
	for (int i = 0; i < num_msg; i++) {
		switch (msg_array[i].msg_style) {
		case PAM_PROMPT_ECHO_OFF: {
				char *pw = malloc(MAX_LEN + 1);
				if (pw == NULL) {
					goto bailout;
				}

				strncpy(pw, password, MAX_LEN);
				resp_array[i].resp = pw;
				resp_array[i].resp_retcode = 0;
			}
			break;
		default:
			goto bailout;
		}
	}
	*resp = resp_array;

	return PAM_SUCCESS;

bailout:
	if (resp_array != NULL) {
		free(resp_array);
	}
	*resp = NULL;
	return PAM_CONV_ERR;
}

// If there is any error, abort the auth process
static void check_pam_error(pam_handle_t *pamh, int status)
{
	if (status != PAM_SUCCESS) {
		printf("ERROR: %s\n", pam_strerror(pamh, status));
		pam_end(pamh, status);
		exit(PAMAUTH_ERROR);
	}
}

static struct pam_conv pc = {auth_conv, NULL};

int main(int argn, const char *argv)
{
	pam_handle_t *pamh;
	int ret = PAM_ABORT;

	username = getenv("username");
	password = getenv("password");

	if ((username == NULL)
			|| (password == NULL)
			|| (strlen(username) > MAX_LEN)
			|| (strlen(password) > MAX_LEN)) {
		printf("Invalide username or password\n");
		return PAMAUTH_ERROR;
	}

    ret = pam_start("login", username, &pc, &pamh);
	check_pam_error(pamh, ret);
	ret = pam_authenticate(pamh, PAM_DISALLOW_NULL_AUTHTOK);
	check_pam_error(pamh, ret);
	pam_end(pamh, ret);

	return ret;
}

