def parse_quotes(file_path: str):
    quotes = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                quote, author = line.strip().split("|", 1)
                quotes.append((quote.strip().strip('"'), author.strip()))
    return quotes
