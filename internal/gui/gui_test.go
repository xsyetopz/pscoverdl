package gui

import (
	"context"
	"os"
	"os/exec"
	"reflect"
	"testing"
)

func TestBuildCLIArgsIncludesSelectedOptions(t *testing.T) {
	args, err := BuildCLIArgs(Config{
		Emulator:     "pcsx2",
		CoverDir:     "/covers",
		GameListPath: "/cache/gamelist.cache",
		CoverType:    "3d",
		Fallback:     true,
		UseHTTP:      true,
		Workers:      8,
	})
	if err != nil {
		t.Fatalf("BuildCLIArgs returned error: %v", err)
	}

	want := []string{
		"-emulator", "pcsx2",
		"-covers", "/covers",
		"-gamelist", "/cache/gamelist.cache",
		"-type", "3d",
		"-workers", "8",
		"-fallback",
		"-http",
	}
	if !reflect.DeepEqual(args, want) {
		t.Fatalf("args=%#v want=%#v", args, want)
	}
}

func TestBuildCLIArgsRejectsMissingRequiredFields(t *testing.T) {
	_, err := BuildCLIArgs(Config{Emulator: "duckstation", CoverType: "default"})
	if err == nil {
		t.Fatal("BuildCLIArgs returned nil error")
	}
}

func TestStartDownloadInvokesCLIWithArguments(t *testing.T) {
	if os.Getenv("PSCOVERDL_GUI_TEST_HELPER") == "1" {
		return
	}

	var gotPath string
	var gotArgs []string
	oldCommandContext := commandContext
	commandContext = func(ctx context.Context, name string, args ...string) *exec.Cmd {
		gotPath = name
		gotArgs = append([]string(nil), args...)
		cmdArgs := []string{"-test.run=TestHelperProcess", "--"}
		cmdArgs = append(cmdArgs, args...)
		cmd := exec.CommandContext(ctx, os.Args[0], cmdArgs...)
		cmd.Env = append(os.Environ(), "PSCOVERDL_GUI_TEST_HELPER=1")
		return cmd
	}
	t.Cleanup(func() { commandContext = oldCommandContext })

	app := NewApp("/bin/pscoverdl")
	result := app.StartDownload(Config{
		Emulator:     "duckstation",
		CoverDir:     "/covers",
		GameListPath: "/cache/gamelist.cache",
		CoverType:    "default",
		Fallback:     true,
		Workers:      6,
	})

	if result.Error != "" {
		t.Fatalf("StartDownload error=%q output=%q", result.Error, result.Output)
	}
	if gotPath != "/bin/pscoverdl" {
		t.Fatalf("path=%q", gotPath)
	}
	want := []string{"-emulator", "duckstation", "-covers", "/covers", "-gamelist", "/cache/gamelist.cache", "-type", "default", "-workers", "6", "-fallback"}
	if !reflect.DeepEqual(gotArgs, want) {
		t.Fatalf("args=%#v want=%#v", gotArgs, want)
	}
}

func TestConfigForEmulatorMatchesLegacyCoverTypeAndSSL(t *testing.T) {
	cfg := ConfigForEmulator("pcsx2", EmulatorConfig{
		CoverDirectory: "/covers",
		GameCache:      "/cache/gamelist.cache",
		CoverType:      1,
		UseSSL:         false,
		Fallback:       true,
	})
	want := Config{Emulator: "pcsx2", CoverDir: "/covers", GameListPath: "/cache/gamelist.cache", CoverType: "3d", UseHTTP: true, Fallback: true, Workers: 4}
	if !reflect.DeepEqual(cfg, want) {
		t.Fatalf("cfg=%#v want=%#v", cfg, want)
	}
}

func TestHelperProcess(_ *testing.T) {
	if os.Getenv("PSCOVERDL_GUI_TEST_HELPER") != "1" {
		return
	}
	_, _ = os.Stdout.WriteString("download complete\n")
	os.Exit(0)
}
