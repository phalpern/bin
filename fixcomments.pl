#! /usr/bin/perl -w

use strict;
use English;

my $STARTCMNT = 1;
my $ENDCMNT = 2;
my $INCMNT = 4;
my $ONELINECMNT = $STARTCMNT | $ENDCMNT | $INCMNT;

my $LARGEBLOCK = 3;  # A block with this many lines is considered large

my $TABSTOP = 8;     # tab stop for hard tabs

# Given a line, determine whether the entire line is a C++-style comment.
# If not, return -1, else return the column at which the comment starts.
sub lineCommentCol
{
    my $line = shift;
    
    if ($line =~ m( (^[ \t]*) //)ox )
    {
	my $whitespace = $1;
	my $col = 0;
	for (my $i = 0; $i < length($whitespace); ++$i)
	{
	    if (substr($whitespace, $i, 1) eq "\t")
	    {
		$col += $TABSTOP;
		$col -= $col % $TABSTOP;
	    }
	    else
	    {
		++$col;
	    }
	}

	return $col;
    }

    return -1;
}

# Replace C++-style comments with appropriate C-style delimiters
sub commentFix
{
    my ($line, $flags, $col, $cmntlines) = @ARG;

    if ($flags == $ONELINECMNT || $flags == 0)
    {
	# Comment begins and ends on same line, or no comment block found.
	# Replace // ... comment with complete /* ... */ comment.
	$line =~ s( // (.*) \n)(/*$1 */\n)ox;
    }
    elsif ($flags & $STARTCMNT)
    {
	# Replace // ... with /* ... (without */)
	$line =~ s( // )(/*)ox;
    }
    elsif ($flags & $ENDCMNT)
    {
	# Replace "//" with " *" (comment continuation
	$line =~ s( // )( *)ox;

	if ($cmntlines >= $LARGEBLOCK)
	{
	    # End large block with */ on separate line at same column
	    
	    # Use hard tab for each $TABSTOP characters of whitespace
	    my $whitespace = substr("\t\t\t\t\t\t\t\t\t\t" .
				    "\t\t\t\t\t\t\t\t\t\t" .
				    "\t\t\t\t\t\t\t\t\t\t" .
				    "\t\t\t\t\t\t\t\t\t\t",
				    0, $col / $TABSTOP);
	    
	    # Use space for remaining characters of whitespace.
	    $whitespace = substr("        ", 0, $col);

	    # Line already ends with newline, simply append additional line
	    $line .= "$whitespace */\n";
	}
	else
	{
	    # Add a */ before the newline
	    $line =~ s( \n$ )( */\n)ox;
	}
    }
    else
    {
	# Replace "//" with " *" (comment continuation)
	$line =~ s( // )( *)ox;
    }
    return $line;
}

my $lastline = "";
my $lastflags = 0;
my $lastcol = -1;
my $lastcmntlines = 0;
my $currline = "x";
my $currcol = -1;
my $currflags = 0;
my $currcmntlines = 0;

while ($currline ne "")
{
    $currline = <STDIN>;
    $currline = "" if (! defined($currline));

    my $currcol = lineCommentCol($currline);

    $currflags = 0;
    if ($currcol >= 0)
    {
	# Full-line //-style comment
	$currflags |= $INCMNT;

	if ($currcol == $lastcol)
	{
	    $currcmntlines = $lastcmntlines + 1;
	}
	else
	{
	    $currcmntlines = 1;
	    $currflags |= $STARTCMNT;
	    $lastflags |= $ENDCMNT if ($lastflags & $INCMNT);
	}
    }
    else
    {
	# Not full-line //-style comment
	$currcmntlines = 0;
	$lastflags |= $ENDCMNT if ($lastflags & $INCMNT);
    }


    print commentFix($lastline, $lastflags, $lastcol, $lastcmntlines);

    $lastline = $currline;
    $lastcol = $currcol;
    $lastflags = $currflags;
    $lastcmntlines = $currcmntlines;
}


