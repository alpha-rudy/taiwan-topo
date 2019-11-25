#!/bin/sh

target=$1
add=$2
end=$3
[ -f ${target} ] || exit 1
[ -f ${add} ] || exit 1
[ -z ${end} ] || exit 1

if [ $(uname) != 'Darwin' ]; then
alias gsed='sed'
fi

let $(osmium fileinfo -e ${target} | \
		gsed -e 's/Largest node ID: /LNID=/' -e 's/Largest way ID: /LWID=/' -e 's/Largest relation ID: /LRID=/' | \
		grep ID=)

let LNID++ LWID++ LRID++

EXT=${target##*.}
REN_FILE="ren_${RANDOM}.pbf"
MGR_FILE="mgr_${RANDOM}.pbf"

echo "renumber ${add}: ${LNID},${LWID},${LRID}"
osmium renumber \
	-s ${LNID},${LWID},${LRID} \
	${add} \
	-Oo ${REN_FILE} || exit $?

echo "merge: ${target} ${add}"
osmium merge \
	${target} \
	${REN_FILE} \
	-Oo ${MGR_FILE} || exit $?

[ "${EXT}" == pbf ] && mv ${MGR_FILE} ${target} || osmconvert ${MGR_FILE} -o=${target}
rm -f ${REN_FILE} ${MGR_FILE}
