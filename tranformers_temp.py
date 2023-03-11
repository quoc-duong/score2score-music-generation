vocabulary = get_vocabulary(dataset_path)
context = [vocabulary.index(context)]

model = ...
model.to(device)
 model.load_state_dict(torch.load(
      Path(model_path, model_name + ".pth"))["model_state_dict"])
  model.eval()

   if start_token is None:
        assert context is not None, 'You must give the start_token or the context'
        context = torch.tensor(context, device=device, dtype=torch.float16).unsqueeze(
            0).repeat(batch_size, 1)
    else:
        assert context is None, 'You must give the start_token or the context'
        context = torch.full((batch_size, 1), start_token,
                             device=device, dtype=torch.float16)

    prev = context
    output = context
    with torch.no_grad():
        # trange(configs["model_configs"]["SEQ_LEN"]):
        for i in trange(seq_len):
            logits = model(output)
            logits = logits[:, -1, :] / temperature
            logits = top_k_logits(logits, k=top_k)
            log_probs = F.softmax(logits, dim=-1)
            if sample:
                prev = torch.multinomial(log_probs, num_samples=1)
            else:
                _, prev = torch.topk(log_probs, k=1, dim=-1)
            output = torch.cat((output, prev), dim=1)
    output = output.to(torch.int)

    logging.info(f"Generated token seq indexes: {output.tolist()[0]}")

    token_seq = indices_to_text(output.tolist()[0], vocabulary)
    logging.info(f"Generated token seq is: {token_seq}")
