using UnityEngine;

public sealed class PulseGate : MonoBehaviour
{
    private int charge;
    private bool opened;
    private bool denied;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Bootstrap()
    {
        new GameObject("Pulse Gate").AddComponent<PulseGate>();
    }

    public string Status => opened ? "Gate open!" :
        denied ? "Pulse needs 2 charges. Try charging first." : $"Charge {charge} / 2";

    public void Play(string action)
    {
        if (action == "Reset")
        {
            charge = 0;
            opened = false;
            denied = false;
        }
        else if (!opened && action == "Charge")
        {
            charge = Mathf.Min(2, charge + 1);
            denied = false;
        }
        else if (!opened && action == "Pulse")
        {
            denied = charge < 2;
            opened = !denied;
            if (opened) charge = 0;
        }
    }

    private void OnGUI()
    {
        GUILayout.BeginArea(new Rect(32, 32, 330, 220), GUI.skin.box);
        GUILayout.Label("Pulse Gate");
        GUILayout.Label(Status);
        foreach (string action in new[] { "Charge", "Pulse", "Reset" })
        {
            if (GUILayout.Button(action, GUILayout.Height(36))) Play(action);
        }
        GUILayout.EndArea();
    }
}
