###################################
sub SD_UT_tristate2bin {
  my $tsData = shift // return;
  my %tristatetobin=(
     '0' => '00',
     'F' => '10',
     '1' => '11'
  );
  my $bitData = '';
  for (my $n=0; $n < length($tsData); $n++) {
    $bitData = $bitData . $tristatetobin{substr($tsData,$n,1)};
  }
  return $bitData;
}

print ("\nZu\n");
print (SD_UT_tristate2bin ("1FFF1F0F0"));

print ("\nAuf\n");
print (SD_UT_tristate2bin ("1FFF1F0FF"));

print ("\n\n");
