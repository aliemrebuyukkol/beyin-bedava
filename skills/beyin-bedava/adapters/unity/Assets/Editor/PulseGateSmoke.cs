using System;
using UnityEngine;

public static class PulseGateSmoke
{
    public static void Run()
    {
        var instance = new GameObject("Smoke");
        try
        {
            var gate = instance.AddComponent<PulseGate>();
            gate.Play("Pulse");
            if (!gate.Status.Contains("needs 2")) throw new Exception(gate.Status);
            gate.Play("Charge");
            gate.Play("Charge");
            gate.Play("Pulse");
            if (gate.Status != "Gate open!") throw new Exception(gate.Status);
            gate.Play("Reset");
            if (gate.Status != "Charge 0 / 2") throw new Exception(gate.Status);
            Debug.Log("Pulse Gate smoke passed");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }
}
