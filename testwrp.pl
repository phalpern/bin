#! /usr/bin/perl -w

use Text::Wrap;

$Text::Wrap::columns = 12;

my $line = "the quick brown fox jumped over the lazy dog\nthe itzy bitzy spider climbed up the water spout\n";

print "[". Text::Wrap::wrap("","",$line) . "]\n";
