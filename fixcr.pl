#! /usr/bin/perl -w

use strict;
use English;

my $copyright = "Copyright (C) 2002 Halpern-Wight Software, Inc. All rights reserved.";

for my $file (@ARGV)
{
    print STDERR "$file...\n";
    if ($file =~ /[Mm]akefile/ || $file =~ /\.mk$/ || $file =~ /\.pl$/)
    {
	system("echo \"# $copyright\" > $file.cr");
	system("echo >> $file.cr");
    }
    elsif ($file =~ /\.[ch]$/ || $file =~ /\.cc/ || $file =~ /\.hh/ ||
	   $file =~ /\.cdl/ || $file =~ /\.[yl]/)
    {
	system("echo \"/* $copyright */\" > $file.cr");
	system("echo >> $file.cr");
    }
    else
    {
	print STDERR "Don't know comment delimiter for $file\n";
    }

    system("sed -e 's/Copyright\\(.* Tenor Networks.*\\)All rights reserved/Portions copyright\\1Used by permission/g' $file >> $file.cr");

    system("mv -f $file.cr $file");
}
