#!/usr/bin/perl
#
# Usage: set-typ.pl <family id> <product id> <TYP file>
#
# Position of bytes in TYP file:
#
# Little-endian
# Bytes 2f-30: Family ID
# Bytes 31-32: Procuct ID

my $familyID = shift(@ARGV);
my $productID = shift(@ARGV);

my $typFile = shift(@ARGV);

my $IDsize = 2;
my $FIDstart = 0x2f;
my $PIDstart = 0x31;

open(TYP, "+<$typFile") || die "Can't update $typFile: $!";
 
print "Updating $typFile...\n";

seek(TYP, $FIDstart, 0);
read(TYP, $FID, $IDsize) == $IDsize || die "can't read FID: $!";

seek(TYP, $PIDstart, 0);
read(TYP, $PID, $IDsize) == $IDsize || die "can't read PID: $!";

my $FIDu = unpack("S", $FID);

my $PIDu = unpack("S", $PID);

print "Original Fid: $FIDu Pid: $PIDu\n";

#-----------------
# Change FID, PID:

seek(TYP, $FIDstart, 0);
print TYP pack('S', $familyID);

seek(TYP, $PIDstart, 0);
print TYP pack('S', $productID);

#-----------------

seek(TYP, $FIDstart, 0);
read(TYP, $FID, $IDsize) == $IDsize || die "can't read FID: $!";

seek(TYP, $PIDstart, 0);
read(TYP, $PID, $IDsize) == $IDsize || die "can't read PID: $!";

$FIDu = unpack("S", $FID);

$PIDu = unpack("S", $PID);

print "Changed Fid: $FIDu Pid: $PIDu\n";

close TYP;

exit;
