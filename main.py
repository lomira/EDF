import torch


def main():
    print("Hello from edf!")
    print(f"Torch version: {torch.__version__}")
    print(f"Torch CUDA available: {torch.cuda.is_available()}")


if __name__ == "__main__":
    main()
