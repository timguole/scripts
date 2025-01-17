#!/bin/bash

target_user=me
if [[ "$USER" != "$target_user" ]]; then
	echo "current user: $USER";
	echo "Re-run as $target_user";
	sudo -u $target_user bash $0 &
	wait;
	exit $?;
fi

sleep 3;
echo $USER $$;
