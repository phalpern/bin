#! /usr/bin/perl -w

use strict;
use English;

use File::Copy;
use File::Basename;

my $file1 = $ARGV[0];
my $file2 = $ARGV[1];
my $basefile1 = basename($file1, ".o");
my $basefile2 = basename($file2, ".o");
my $strip1 = "/tmp/bincmp1.strip";
my $strip2 = "/tmp/bincmp2.strip";

copy($file1, "$strip1") or die "Can't copy $file1\n";
copy($file2, "$strip2") or die "Can't copy $file2\n";


system("strip", "$strip1");
system("strip", "$strip2");

open FILE1, "< $strip1" or die "Can't open $strip1\n";
open FILE2, "< $strip2" or die "Can't open $strip2\n";
binmode *FILE1;
binmode *FILE2;

my $dump1 = $strip1."dump";
my $dump2 = $strip2."dump";
open DUMP1, "> $dump1" or die "Can't open $dump1 for write\n";
open DUMP2, "> $dump2" or die "Can't open $dump2 for write\n";
binmode *DUMP1;
binmode *DUMP2;

my $linecount = 0;
my $charcount = 0;
my $diff = 0;

local $/ = undef; # Disable line breaks
while (1)
{
    my $line1 = <FILE1>;
    my $line2 = <FILE2>;

    last unless (defined($line1) || defined($line2));

    $diff = 1;

    $linecount += 1;

    last unless (defined($line1) && defined($line2));

    my $newcharcount = $charcount += length($line1);

    if ($line1 ne $line2)
    {
        $line1 =~ s/\$Id:[^\$]*\$//go ;
        $line1 =~ s/\$Header:[^\$]*\$//go ;
        $line1 =~ s/__unnamed_[^_]*_/__unamed_namespace_::/go ;
        $line1 =~ s/\.L[A-Za-z0-9]*/.Llabel/go ;
        $line1 =~ s/\$X[^. \0]*\.//go ;
        $line1 =~ s(\0/[^\0]*$basefile1\.cpp\0)(\0$basefile1.cpp\0)go ;

        $line2 =~ s/\$Id:[^\$]*\$//go ;
        $line2 =~ s/\$Header:[^\$]*\$//go ;
        $line2 =~ s/__unnamed_[^_]*_/__unamed_namespace_::/go ;
        $line2 =~ s/\.L[A-Za-z0-9]*/.Llabel/go ;
        $line2 =~ s/\$X[^. \0]*\.//go ;
        $line2 =~ s(\0/[^\0]*$basefile2\.cpp\0)(\0$basefile1.cpp\0)go ; # basefile1 not 2
    }

    print DUMP1 $line1;
    print DUMP2 $line2;

    last unless ($line1 eq $line2);

    $charcount = $newcharcount;

    $diff = 0;
}

close DUMP1;
close DUMP2;

if ($diff)
{
    print STDERR "Files differ: $file1 and $file2\n";
    system("cmp", $dump1, $dump2);
#         for (my $i = 1; $i <= length($line1); ++$i) {
#             if (substr($line1, $i - 1, 1) ne substr($line2, $i - 1, 1)) {
#                 print STDERR "At line $linecount, character $i\n";
#                 last;
#             }
#         }
    exit 1;
}
# else
# {
#     printf STDERR ("Files are the same.\n");
# }
