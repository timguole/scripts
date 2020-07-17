# Join values with delimiter
# join <delimiter> <value1> <value2> ...
# The result is: <v><d><v><d><v>...
function join()
{
	local delimit=$1;
	local f1=$2;
	local v='';
	
	shift; # shift delimiter
	shift; # shift the first field
	for m in "$@"; do
		v=$v$delimit$m;
	done

	echo $f1$v;
}

# Split string into fields by delimiter, and
# get field value of the index number
# get_field <delimiter> <string> <field-index>
function get_field()
{
    local _old_ifs="$IFS";
    IFS="$1";
    local _a=($2);
    IFS="$_old_ifs";
    echo ${_a[$3]};
}

