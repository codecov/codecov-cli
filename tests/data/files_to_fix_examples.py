cpp_file = """
{ // wubba lubba dub dub
    
}
// LCOV_EXCL_BEGIN
Hello
// LCOV_EXCL_START
// LCOV_EXCL_END
{
    
}
not empty
// LCOV_EXCL_STOP
"""
php_file = """
fadsfa ds(

);

asdfasdf(

);     // msa

[ffapsdojf, fasdpofja sd,fasdjfpo]

    [ // abc
    
        fasdjfpasd,
        fasdjfpas,
        fasdpfj,
    ]
"""

go_file = """
abc at line 3
xyz at line 6

// comment at line
	// another comment
{
	asdfadsf
}
{ // hey

}
func { 

}

func { // fapsodjfpjasdpf jaspdfj 

}

/*

*/
	/*
	*/

"""


kt_file = """{
    first line on kotlin file
}

secnod line

{
    previous line should be fixed
}


{ // afsdpfjasd fjasdpfj apsdjf
    should fix previous
}


    /*


    some stuff here

*/




// fasdpofjaspdf


// fapsjdf
"""
