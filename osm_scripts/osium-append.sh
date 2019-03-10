#!/bin/sh

target=$1
add=$2
end=$3
[ -f $target ] || exit 1
[ -f $add ] || exit 1
[ -z $end ] || exit 1

if [ $(uname) != 'Darwin' ]; then
alias gsed='sed'
fi

let $(osmium fileinfo -e $target | \
		gsed -e 's/Largest node ID: /LNID=/' -e 's/Largest way ID: /LWID=/' | \
		grep ID=)

let LNID++ LWID++

REN_FILE="ren_${RANDOM}.pbf"
MGR_FILE="mgr_${RANDOM}.pbf"

echo "renumber $add: ${LNID},${LWID},0"
osmium renumber \
	-s ${LNID},${LWID},0 \
	$add \
	-Oo ${REN_FILE}

echo "merge: $target $add"
osmium merge \
	$target \
	${REN_FILE} \
	-Oo ${MGR_FILE}

rm -f ${REN_FILE}
mv ${MGR_FILE} $target
