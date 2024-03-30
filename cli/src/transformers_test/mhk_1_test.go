package transformers_test

import (
	"testing"
)

func Test_PackMhk1(t *testing.T) {
	ok, err := comparePacked("mhk_1")
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	if !ok {
		t.Fatalf("Packed file does not match expected data.")
	}
}

func Test_UnpackMhk1(t *testing.T) {
	ok, err := compareUnpacked("mhk_1")
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	if !ok {
		t.Fatalf("Unpacked files do not match expected data.")
	}
}